// Extracted bundle file 73; see extract.py and README.md.
using System;
using System.Collections.Generic;
using Orvex.Model.WSX_Specific_Model;

namespace Orvex.Model
{
    public class ChildGeneral
    {
        public ChildGeneral()
        {
            HlxAppointment = new List<HlxAppointment>();
            ChildExamination = new List<ChildExamination>();
            ChildMeasurement = new List<ChildMeasurement>();
            ChildPreschoolRecall = new List<ChildPreschoolRecall>();
            Consents = new List<Consent>();
            ChildSchoolRecall = new List<ChildSchoolRecall>();

            WsxEnterResultProgress = new List<WsxEnterResultProgress>();

        }

        public long ClientId { get; set; }
        public string Sector { get; set; }
        public DateTime DateOfBirth { get; set; }
        public DateTime? DateOfDeath { get; set; }
        public string Sex { get; set; }
        public string RecordStatus { get; set; }

        public virtual ICollection<HlxAppointment> HlxAppointment { get; set; }
        public virtual ICollection<ChildExamination> ChildExamination { get; set; }
        public virtual ChildLocations ChildLocations { get; set; }
        public virtual ChildLocations ChildLocations1 { get; set; }
        public virtual ICollection<ChildMeasurement> ChildMeasurement { get; set; }
        public virtual ICollection<ChildPreschoolRecall> ChildPreschoolRecall { get; set; }
        public virtual ICollection<Consent> Consents { get; set; }
        public virtual ICollection<ChildSchoolRecall> ChildSchoolRecall { get; set; }

        public virtual ICollection<WsxEnterResultProgress> WsxEnterResultProgress {get; set;}

    }
}
