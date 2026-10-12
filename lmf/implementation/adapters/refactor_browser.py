#!/usr/bin/env python3
"""Actual browser gate. Requires Playwright/Chromium; no fallback success."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright


def verify(url, root):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        page.wait_for_selector('#save')
        # Wait for interactive handlers, not just server prerendered HTML.
        page.wait_for_selector('form[data-interactive="True"]')
        assert page.locator('#Heart option').all_text_contents() == ['1 - Satisfactory', '2 - Concern', '3 - Not assessed', '']
        page.locator('#Heart').select_option('1')
        page.locator('#Hips').select_option('2')
        page.locator('#Eyes').select_option('3')
        page.locator('#Testes').select_option('1')
        page.locator('#PhysicalGeneral').select_option('2')
        page.locator('#Height').fill('55')
        page.locator('#Weight').fill('4')
        page.locator('#HeadCircumference').fill('35')
        page.locator('#save').click()
        page.wait_for_selector('#saved article')
        first = page.locator('#saved').inner_text()
        for value in ('"Heart": 1', '"Hips": 2', '"Eyes": 3', '"Testes": 1', '"PhysicalGeneral": 2', '"ClientId": 1001', '"HeadCircumference": 35'):
            assert value in first, value
        page.reload()
        page.wait_for_selector('#saved article')
        page.wait_for_selector('form[data-interactive="True"]')
        assert page.locator('#saved').inner_text() == first, 'Reload lost read-back'
        assert page.locator('#contact option').all_text_contents() == ['KD03']
        assert page.locator('#contact').is_disabled()
        page.locator('#ExaminationDate').fill('2025-02-21')
        page.locator('#Heart').select_option('1')
        page.locator('#HeadCircumference').fill('100')
        page.locator('#save').click()
        page.wait_for_function("() => document.querySelector('#outcome').textContent.includes('HeadCircumferenceInvalidFormatMessage')")
        assert page.locator('#saved article').count() == 1, 'Invalid input saved'
        page.locator('#HeadCircumference').fill('35')
        page.locator('#save').click()
        page.wait_for_selector('#confirm')
        assert 'KdpDuplicateExamCodeMessage' in page.locator('#outcome').inner_text()
        assert page.locator('#saved article').count() == 1, 'Unconfirmed warning saved'
        page.locator('#cancel').click()
        assert page.locator('#saved article').count() == 1
        page.locator('#save').click()
        page.wait_for_selector('#confirm')
        page.locator('#confirm').click()
        page.wait_for_function("() => document.querySelectorAll('#saved article').length === 2")
        readback = page.locator('#saved').inner_text()
        assert 'Repeat: True' in readback and 'Repeat: False' in readback
        page.reload()
        page.wait_for_function("() => document.querySelectorAll('#saved article').length === 2")
        assert page.locator('#saved').inner_text() == readback
        assert not errors, errors
        page.screenshot(path=str(root / 'browser.png'), full_page=True)
        browser.close()
    checks = ['kd03-add-fields-read-back', 'reload-retains-persistence', 'unsupported-not-offered',
              'invalid-field-no-save', 'warning-cancel-no-save', 'confirmed-second-result-repeat-read-back']
    (root / 'browser-report.json').write_text(json.dumps({'passed': len(checks), 'failed': 0, 'skipped': 0,
        'checks': checks, 'url': url, 'browser': 'Playwright Chromium', 'pageErrors': errors}, indent=2) + '\n')


if __name__ == '__main__':
    verify(sys.argv[1], Path(sys.argv[2]))
