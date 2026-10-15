import assert from 'node:assert/strict';

// WCAG relative luminance, sRGB linearisation, and (Llighter + .05)/(Ldarker + .05).
function ratio(a, b) {
  const luminance = rgb => rgb.slice(0, 3).map(v => {
    const s = v / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  }).reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
  const x = luminance(a), y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
assert.equal(ratio([0, 0, 0], [255, 255, 255]), 21);
assert.equal(ratio([255, 255, 255], [255, 255, 255]), 1);

export async function measureContrast(page, report, state, selector, focus = false) {
  report.contrast ??= {
    method: 'Chromium computed sRGB colours, alpha-composited over rendered ancestor backgrounds; WCAG relative luminance. No colour rounding before threshold comparison.',
    criteria: '1.4.3: 4.5:1 normal text, 3:1 large text (24px or 18.667px bold). 1.4.11: 3:1 control boundaries and contrasting focus indicator portions. Visible keyboard focus also checked separately (2.4.7). Not a full WCAG audit or AAA 2.4.13 claim.',
    measurements: []
  };
  const samples = await page.locator(selector).evaluateAll((elements, focused) => {
    const rgba = value => {
      const match = value.match(/^rgba?\(([^)]+)\)$/);
      if (!match) throw new Error(`Unsupported computed colour: ${value}`);
      const values = match[1].split(',').map(Number);
      return [...values.slice(0, 3), values[3] ?? 1];
    };
    const over = (a, b) => a.slice(0, 3).map((v, i) => v * a[3] + b[i] * (1 - a[3]));
    const background = el => {
      if (!el) return [255, 255, 255]; // Browser's default opaque canvas.
      const style = getComputedStyle(el);
      // The reviewed select SVG is a separate right-aligned icon, not behind text.
      const selectIcon = el.matches('.nhsw-select') &&
        decodeURIComponent(style.backgroundImage).includes("fill='#212B32'") &&
        style.backgroundSize === '10px 16px' && style.paddingRight === '32px';
      if ((style.backgroundImage !== 'none' && !selectIcon) || style.opacity !== '1') {
        throw new Error('Image/opacity needs pixel-based contrast measurement');
      }
      return over(rgba(style.backgroundColor), background(el.parentElement));
    };
    return elements.filter(el => el.getClientRects().length).map(el => {
      const visual = focused && el.matches('.nhsw-site-header__nav-link') ? el.querySelector('span') : el;
      const s = getComputedStyle(visual), bg = background(visual), outside = background(el.parentElement);
      const after = getComputedStyle(visual, '::after');
      return {
        element: el.id ? `#${el.id}` : `${el.tagName.toLowerCase()}.${el.className}`,
        text: (el instanceof HTMLInputElement ? el.value : el.textContent).trim(),
        fontSize: parseFloat(s.fontSize), fontWeight: s.fontWeight,
        foreground: over(rgba(s.color), bg), background: bg, outside,
        control: el.matches('input, select, button, .nhsw-error-summary'),
        selectIcon: el.matches('.nhsw-select') && s.backgroundImage !== 'none',
        border: over(rgba(s.borderTopColor), bg), borderWidth: s.borderTopWidth,
        focused, outline: s.outline, shadow: s.boxShadow,
        pseudoIndicator: after.content !== 'none' && after.content !== 'normal' && parseFloat(after.height) >= 3
          ? over(rgba(after.backgroundColor), outside) : null,
        // Current NHSW uses one solid shadow for the select/input/button focus.
        shadowColour: s.boxShadow === 'none' ? null : over(rgba(s.boxShadow.match(/rgba?\([^)]+\)/)[0]), outside),
        outlineColour: over(rgba(s.outlineColor), outside)
      };
    });
  }, focus);
  assert.ok(samples.length, `No rendered samples for ${state}: ${selector}`);
  const rows = report.contrast.measurements;
  const add = (sample, kind, foreground, background, threshold, criterion) => {
    const measured = ratio(foreground, background);
    rows.push({ state, element: sample.element, text: sample.text,
      fontSize: sample.fontSize, fontWeight: sample.fontWeight, kind, foreground, background,
      ratio: measured, threshold, criterion, passed: measured >= threshold });
  };
  for (const s of samples) {
    const large = s.fontSize >= 24 || (s.fontSize >= 18.6666666667 && Number(s.fontWeight) >= 700);
    add(s, 'text', s.foreground, s.background, large ? 3 : 4.5, '1.4.3');
    if (s.selectIcon) add(s, 'reviewed rendered select SVG arrow / background', [33, 43, 50], s.background, 3, '1.4.11');
    if (focus && !s.control) {
      assert.equal(await page.locator(selector).evaluate(el => el === document.activeElement), true);
      const indicator = s.shadowColour ?? s.pseudoIndicator;
      assert.ok(indicator, 'NHSW link keyboard focus needs its dark underline: ' + JSON.stringify(s));
      // Reverse header links use the yellow fill against the dark header; the
      // dark underline qualifies against the focused yellow text background.
      add(s, 'link focus underline / focused background', indicator, s.background, 3, '1.4.11');
      const outsideRatio = ratio(indicator, s.outside);
      add(s, outsideRatio >= 3 ? 'link underline / surroundings' : 'link focused fill / surroundings',
        outsideRatio >= 3 ? indicator : s.background, s.outside, 3, '1.4.11');
    }
    if (!s.control) continue;
    if (!focus) {
      // Filled primary button is identified by its fill; outlined controls by border.
      const filled = s.element.includes('nhsw-button--primary');
      add(s, filled ? 'button fill / surrounding page' : 'boundary / surrounding page',
        filled ? s.background : s.border, s.outside, 3, '1.4.11');
    } else {
      assert.equal(await page.locator(selector).evaluate(el => el === document.activeElement), true);
      if (s.element.startsWith('button.')) {
        assert.notEqual(s.shadow, 'none', 'NHSW button focus needs its dark underline');
        add(s, 'focus underline / surrounding page', s.shadowColour, s.outside, 3, '1.4.11');
        add(s, 'focus underline / yellow fill', s.shadowColour, s.background, 3, '1.4.11');
      } else if (s.element.includes('nhsw-error-summary')) {
        assert.ok(s.outline.includes('solid') && s.outline.includes('3px'), 'Error summary focus must retain the official outline');
        add(s, 'focus error border / yellow outline', s.border, s.outlineColour, 3, '1.4.11');
        add(s, 'focus error border / surrounding page', s.border, s.outside, 3, '1.4.11');
      } else {
        assert.notEqual(s.shadow, 'none', 'NHSW control focus needs its dark inset edge');
        add(s, 'focus dark edge / control background', s.shadowColour, s.background, 3, '1.4.11');
        add(s, 'focus dark border / yellow outline', s.border, s.outlineColour, 3, '1.4.11');
        add(s, 'focus dark border / surrounding page', s.border, s.outside, 3, '1.4.11');
      }
      // Yellow alone is not the qualifying indicator; retain the low contrast too.
      rows.push({ state, element: s.element, kind: 'yellow / page (diagnostic, not sole indicator)',
        foreground: s.element.startsWith('button.') ? s.background : s.outlineColour,
        background: s.outside, ratio: ratio(s.element.startsWith('button.') ? s.background : s.outlineColour, s.outside),
        threshold: null, criterion: 'Informational: qualifying dark focus portions measured above',
        style: { outline: s.outline, shadow: s.shadow } });
    }
  }
  const failures = rows.filter(row => row.passed === false);
  assert.deepEqual(failures, [], 'Rendered contrast must meet applicable AA thresholds');
}
