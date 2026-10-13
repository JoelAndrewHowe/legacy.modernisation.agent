// Extracted bundle file 34; see extract.py and README.md.
namespace Orvex.Messages
{
    /// <summary>
    /// A message class to indicate that a minor issue has occurred.
    /// </summary>
    public class WarningNotificationMessage: MessageBase
    {
        public WarningNotificationMessage(string message, string title = null, string prompt = null) : base(message,title, prompt)
        {
        }
    }
}
