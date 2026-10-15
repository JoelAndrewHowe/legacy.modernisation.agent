// Local-demo preference only; no patient information or draft is stored here.
window.hcwpLanguage = {
    read: () => { try { return localStorage.getItem('hcwp.language') === 'cy' ? 'cy' : 'en'; } catch { return 'en'; } },
    apply: code => {
        document.documentElement.lang = code === 'cy' ? 'cy' : 'en';
        try { localStorage.setItem('hcwp.language', document.documentElement.lang); } catch { /* Circuit-only preference when storage is blocked. */ }
    }
};
// Set language before the interactive circuit starts; later changes do not navigate.
document.documentElement.lang = window.hcwpLanguage.read();
