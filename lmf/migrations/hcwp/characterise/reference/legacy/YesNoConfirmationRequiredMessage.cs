// Extracted bundle file 35; see extract.py and README.md.
using System;

namespace Orvex.Messages
{
    /// <summary>
    /// A message class to indicate that a Non-fatal error has occurred.
    /// </summary>
    public class YesNoConfirmationRequiredMessage : ConfirmationMessageBase
    { 
        public YesNoConfirmationRequiredMessage(string message, string title = null, string prompt = null, Action<bool> onConfirmation = null) 
            : base(message,title, prompt, onConfirmation)
        {
        }
    }
}
