// Extracted bundle file 81; see extract.py and README.md.
using System;
using System.Collections.Generic;
using Orvex.Model.Extensions;
using Orvex.Contracts.Enums;

namespace Orvex.Model
{
    public class ExaminationDescriptions : IActiveDateRange
    {
        public ExaminationDescriptions()
        {
            HlxAppointment = new List<HlxAppointment>();
            ChildExamination = new List<ChildExamination>();
            ChildPreschoolRecall = new List<ChildPreschoolRecall>();
            ChildSchoolRecall = new List<ChildSchoolRecall>();
            PreschoolScheduleExams = new List<PreschoolScheduleExams>();
        }

        public string PkExamDescriptionId { get; set; }
        public ExamType FkExamDescriptionType { get; set; }
        public string LongDescription { get; set; }
        public string ShortDescription { get; set; }
        public string RoutineExam { get; set; }
        public string RecordStatus { get; set; }
        public DateTime? ActiveFrom { get; set; }
        public DateTime? ActiveTo { get; set; }
        public virtual ICollection<HlxAppointment> HlxAppointment { get; set; }
        public virtual ICollection<ChildExamination> ChildExamination { get; set; }
        public virtual ICollection<ChildPreschoolRecall> ChildPreschoolRecall { get; set; }
        public virtual ICollection<ChildSchoolRecall> ChildSchoolRecall { get; set; }
        public virtual ICollection<PreschoolScheduleExams> PreschoolScheduleExams { get; set; }
    }
}
