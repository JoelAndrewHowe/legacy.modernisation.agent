// Extracted bundle file 32; see extract.py and README.md.
namespace Orvex.Messages
{
    /// <summary>
    /// A message class to indicate that a Non-fatal error has occurred.
    /// </summary>
    public class NonFatalErrorEncountered : MessageBase
    {
        public NonFatalErrorEncountered(string message, string title = null, string prompt = null) : base(message, title, prompt)
        {

        }
    }
}
