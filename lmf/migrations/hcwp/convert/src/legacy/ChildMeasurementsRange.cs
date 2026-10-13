// Extracted bundle file 12; see extract.py and README.md.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;
using System.Text;
using System.Threading.Tasks;
using HLX.BusinessTier.Common.Util;

namespace Orvex.TransferObjects
{
    [DataContract]
    public struct ChildMeasurementsRange
    {
        [DataMember]
        public string MeasurementType;
        [DataMember]
        public double UpperBound;
        [DataMember]
        public double LowerBound;
    }
}
