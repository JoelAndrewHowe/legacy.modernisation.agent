using System.Linq; using Orvex.Model; using Orvex.Services.Internal;
namespace Orvex.Business.Utils { public class ExaminationsCrudManager {
        internal static void UpdateRepeatFlags(IUnitOfWork uow, long clientId, string examinationCode)
        {
            var examPrefix = examinationCode.Length > 2 ? examinationCode.Substring(0, 2) : examinationCode;

            //Query database to ensure all exam details are in local cache
            uow.Repository<ChildExaminationGiven>()
                .Include(e => e.ChildExamination)
                .Where(exam => exam.ChildExamination.ClientId == clientId && exam.ChildExamination.FkExaminationId.StartsWith(examPrefix))
                .ToList();

            //Set ChildExamination navigation property to allow querying against local cache
            foreach (var ceg in uow.Repository<ChildExaminationGiven>().Local().Where(ce => ce.ChildExamination == null))
            {
                ceg.ChildExamination = uow.Repository<ChildExamination>().Local().Single(ce => ce.PkChildExaminationId == ceg.PkFkChildExamGivenId);
            }
            
            //Fetch exams that where value of IsRepeat is incorrect and derive correct value
            var examsToUpdate = 
                from exam in uow.Repository<ChildExaminationGiven>().Local()
                where exam.ChildExamination.ClientId == clientId && exam.ChildExamination.FkExaminationId.StartsWith(examPrefix)
                group exam by exam.ChildExamination.FkExaminationId into grp
                let minExamDate = grp.Min(g => g.ExaminationDate)
                from g in grp
                where (g.ExaminationDate > minExamDate && g.ChildExamination.IsRepeat != "Y") || (g.ExaminationDate == minExamDate && g.ChildExamination.IsRepeat != "N")
                select new { g.ChildExamination, IsRepeat = (g.ExaminationDate == minExamDate) ? "N" : "Y" };

            foreach (var item in examsToUpdate)
            {
                item.ChildExamination.IsRepeat = item.IsRepeat;
            }
        }

// Excluded infrastructure boundaries: intentionally no-op.
internal static void UpdateAppointmentStatuses(IUnitOfWork u, string c, long p, long i) {}
internal static void ClearProducedRecalls(IUnitOfWork u, string c, long p) {}
}}
