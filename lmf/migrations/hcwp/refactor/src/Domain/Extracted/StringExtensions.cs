// Extracted bundle file 25; see extract.py and README.md.
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Linq;
using System.Text.RegularExpressions;

namespace OrvexBusinessTierCommon.HLX.BusinessTier.Common.Util
{
    public static class StringExtensions
    {
        public static string ToTitleCase(this string val)
        {
            if (string.IsNullOrEmpty(val)) return "";

            return CultureInfo.InvariantCulture.TextInfo.ToTitleCase(val);
        }

        public static string CamelToUpperUnderscored(this string name)
        {
            var result = Regex.Replace(name, "[a-z][A-Z]", m => m.Value[0] + "_" + m.Value[1]);

            return result.ToUpper();
        }
        public static string CamelToSpacedText(this string name)
        {
            var result = Regex.Replace(name, "[a-z][A-Z]", m => m.Value[0] + " " + m.Value[1]);

            return result;
        }
        public static string StripPunctuation(this string s)
        {
            var sb = new StringBuilder();
            foreach(char c in s)
            {
                if(!char.IsPunctuation(c)) sb.Append(c);
            }
            return sb.ToString();
        }


        public static string LowerCaseSentenceToCamelCaseSentence(this string name)
        {


            string result = Regex.Replace(name, @"\b[a-z]", m => m.ToString().ToUpper(), RegexOptions.None);
            result = Regex.Replace(result, @"(?<=\b[A-Z])\w+", m => m.ToString().ToLower(), RegexOptions.None);

            return result;

        }

        /// <summary>
        /// Method returns input string ,but returns "" if string is null or empty
        /// </summary>
        /// <param name="input"></param>
        /// <returns></returns>
        public static string SafeNotNullValue(this string input)
        {

            if(string.IsNullOrEmpty(input))
            {
                return "";
            }
            return input;
        }

        /// <summary>
        /// Function returns false if string is null or whitespace
        /// </summary>
        /// <param name="input"></param>
        /// <returns></returns>
        public static bool StringTextExists(this string input)
        {

            return !string.IsNullOrWhiteSpace(input);
        }

        public static string TrimToMaxLength(this string input, int max)
        {
            if (string.IsNullOrEmpty(input)) return "";
            if (max == 0) max = input.Length;
            return input.Length > max ? input.Substring(0, max) : input ;
        }
    }
}
