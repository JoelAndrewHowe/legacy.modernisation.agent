// Extracted bundle file 33; see extract.py and README.md.
using System;
using System.Collections.Generic;
using Orvex.TransferObjects;

// ReSharper disable once CheckNamespace
namespace Orvex.Messages
{
   public class ShowFormLookup
    {
        public List<LookupsSubTO> ListToDisplay { get; set; }
        public string Values { get; set; }
        public string Descriptions { get; set; }
        public Action<string, string> OnConfirmation { get; set; }

        public ShowFormLookup(List<LookupsSubTO> listToDisplay, Action<string, string> onConfirmation = null)
        {
            ListToDisplay = listToDisplay;
            OnConfirmation = onConfirmation;
        }
    }
}
