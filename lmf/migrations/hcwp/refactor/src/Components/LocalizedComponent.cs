using Hcwp.Presentation;
using Microsoft.AspNetCore.Components;

namespace Hcwp.Components;

public abstract class LocalizedComponent : ComponentBase, IDisposable
{
    [Inject] protected InterfaceLanguage Language { get; set; }
    protected string T(string text) => Language.Text(text);
    protected string F(string text, params object[] values) => Language.Format(text, values);
    protected override void OnInitialized() => Language.Changed += RefreshLanguage;
    private void RefreshLanguage() => _ = InvokeAsync(StateHasChanged);
    public virtual void Dispose() => Language.Changed -= RefreshLanguage;
}
