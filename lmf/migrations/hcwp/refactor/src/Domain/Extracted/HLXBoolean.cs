// Extracted bundle file 28; see extract.py and README.md.

namespace HLX.Net2008.Common
{
    public static class HLXBoolean
    {
        public const string True = "Y";
        public const string False = "N";

        public static bool HLXBooleanToBoolean(string hlxBoolean)
        {
            return hlxBoolean == True;
        }

        public static string BoolToChar(bool booleanValue)
        {
            return booleanValue ? True : False;
        }
    }
}
