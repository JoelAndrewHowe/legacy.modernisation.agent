// Extracted bundle file 86; see extract.py and README.md.
using System;
using System.Collections.Generic;
using Orvex.Model.Extensions;

namespace Orvex.Model
{
    public class PreschoolScheduleExams : IActiveDateRange
    {
        public short PkScheduleExamId { get; set; }
        public short FkPreschoolScheduleId { get; set; }
        public string FkExamCode { get; set; }
        public string FkExaminerId { get; set; }
        public DateTime? ActiveFrom { get; set; }
        public DateTime? ActiveTo { get; set; }
        public decimal? MinimumAgeWks { get; set; }
        public decimal? MaximumAgeWks { get; set; }
        public decimal? MinimumIntervalWks { get; set; }
        public DateTime? DobFrom { get; set; }
        public DateTime? DobTo { get; set; }
        public string ParentGuardianLabelsRqrd { get; set; }
        public string PhysicalTest { get; set; }
        public string VisionTest { get; set; }
        public string HearingTest { get; set; }
        public string LocomotionTest { get; set; }
        public string ManipulationTest { get; set; }
        public string SpeechLangTest { get; set; }
        public string BehaviourTest { get; set; }
        public string LocalTest1Name { get; set; }
        public string LocalTest1 { get; set; }
        public string LocalTest2Name { get; set; }
        public string LocalTest2 { get; set; }
        public string LocalTest3Name { get; set; }
        public string LocalTest3 { get; set; }
        public string LocalTest4Name { get; set; }
        public string LocalTest4 { get; set; }
        public string HomeAssessment { get; set; }
        public string RecordStatus { get; set; }
        public virtual ExaminationDescriptions ExaminationDescriptions { get; set; }
        public virtual Examiner Examiner { get; set; }
    }
}
