using System; using System.Collections.Generic; using System.Linq; using AutoMapper; using HLX.BusinessTier.Common.Util; using Orvex.Business.Utils; using Orvex.Business.Validation; using Orvex.Model; using Orvex.Services; using Orvex.Services.Internal; using Orvex.TransferObjects; using Orvex.Contracts.Enums;
namespace Orvex.Business { public class KdpExaminationService : IKdpExaminationService {
private readonly Func<IUnitOfWork> unitOfWorkFactory; private readonly KdpExaminationValidator kdpExaminationValidator; private const byte PreschoolConsentCategory=2, MedicalConsentType=11; private const string kdpConsentYesValue="Y";
public KdpExaminationService(Func<IUnitOfWork> factory, KdpExaminationValidator validator) { unitOfWorkFactory=factory; kdpExaminationValidator=validator; }
        public KdpExaminationTO GetKdpExamination(long clientId)
        {
            using (var uow = unitOfWorkFactory())
            {
                var childExamination = uow.Repository<ChildExamination>()
                    .Include(c => c.ChildExaminationGiven)
                    .Include(c => c.ChildExaminationGiven.ChildExaminationKdp)
                    .Include(c => c.ChildMeasurement)
                    .Include(c => c.ExaminationDescriptions)
                    .Include(c => c.ChildExaminationGiven.ChildLocations)
                    .Include(c => c.ChildExaminationGiven.HealthCareProfessionals)
                    .Where(c => c.ClientId == clientId && c.ExaminationDescriptions.FkExamDescriptionType == ExamType.Kdp)
                    .OrderByDescending(c => c.ChildExaminationGiven.ExaminationDate)
                    .ToList();

                var childDetails = GetChildDetails(clientId, uow);

                var outstandingResults = GetKdpOutstandingAppointments(clientId, uow);

                return new KdpExaminationTO
                {
                    Id = clientId.ToString("D"),
                    DateOfBirth = childDetails.DateOfBirth,
                    DateOfDeath = childDetails.DateOfDeath,
                    Gender = childDetails.Sex,
                    HasPreschoolConsent = childDetails.Consents.SingleOrDefault(con => con.ConsentCategory == PreschoolConsentCategory && con.ConsentType == MedicalConsentType)?.ConsentResult == kdpConsentYesValue,
                    HcpExaminationResultToList = childExamination.Select(GetKdpResultTo).ToList(),
                    OutstandingAppointmentsList = outstandingResults
                };
            }
        }
        private static ChildGeneral GetChildDetails(long clientId, IUnitOfWork uow)
        {
            return uow.Repository<ChildGeneral>()
                .Include(cg => cg.Consents)
                .Single(cg => cg.ClientId == clientId);
        }
        public static KdpExaminationResultTO GetKdpResultTo(ChildExamination childExamination)
        {
            var kdpResultTo = childExamination.To<KdpExaminationResultTO>();

            if (childExamination.ChildExaminationGiven != null)
            {
                Mapper.Map(childExamination.ChildExaminationGiven, kdpResultTo);

                if (childExamination.ChildExaminationGiven.ChildExaminationKdp != null)
                {
                    Mapper.Map(childExamination.ChildExaminationGiven.ChildExaminationKdp, kdpResultTo);
                }
            }

            var childMeasurement = childExamination.ChildMeasurement.SingleOrDefault();
            if (childMeasurement != null)
            {
                Mapper.Map(childMeasurement, kdpResultTo);
            }
            kdpResultTo.GenerateLock();
            kdpResultTo.PropertyChanged.Clear();
            return kdpResultTo;
        }
        public KdpExaminationResultTO GetKdpExaminationResult(long pkChildExaminationId)
        {
            using (var uow = unitOfWorkFactory())
            {
                var childExamination = uow.Repository<ChildExamination>()
                    .Include(c => c.ChildExaminationGiven)
                    .Include(c => c.ChildExaminationGiven.ChildExaminationKdp)
                    .Include(c => c.ChildMeasurement)
                    .Include(c => c.ExaminationDescriptions)
                    .Include(c => c.ChildExaminationGiven.ChildLocations)
                    .Include(c => c.ChildExaminationGiven.HealthCareProfessionals)
                    .FirstOrDefault(c => c.PkChildExaminationId == pkChildExaminationId);
          
                return GetKdpResultTo(childExamination);
            }
        }
        public void SaveKdpExaminationResult(KdpExaminationTO kdpExamTo, KdpExaminationResultTO kdpExamResultTo)
        {
            using (var uow = unitOfWorkFactory())
            {
                var currentData = uow.Repository<ChildExamination>()
                    .Include(ce => ce.ChildExaminationGiven)
                    .Include(ce => ce.ChildExaminationGiven.ChildExaminationKdp)
                    .Include(ce => ce.ChildMeasurement)
                    .SingleOrDefault(c => c.PkChildExaminationId == kdpExamResultTo.PkChildExaminationId);

                if (currentData != null)
                {
                    kdpExamResultTo.CheckLock(GetKdpResultTo(currentData));
                    kdpExaminationValidator.ValidateOnSave(kdpExamResultTo, kdpExamTo.DateOfBirth, kdpExamTo.DateOfDeath,kdpExamTo.HcpExaminationResultToList);
                    UpdateKdpExaminationResult(uow, kdpExamResultTo, currentData);
                }
                else
                {
                    kdpExaminationValidator.ValidateOnSave(kdpExamResultTo, kdpExamTo.DateOfBirth, kdpExamTo.DateOfDeath,kdpExamTo.HcpExaminationResultToList);
                    InsertKdpExaminationResult(uow, kdpExamResultTo);
                }

                ExaminationsCrudManager.UpdateRepeatFlags(uow, kdpExamResultTo.ClientId,kdpExamResultTo.ExaminationCode);

                ExaminationsCrudManager.UpdateAppointmentStatuses(uow, kdpExamResultTo.ExaminationCode, kdpExamResultTo.ClientId, kdpExamResultTo.PkChildExaminationId);

                ExaminationsCrudManager.ClearProducedRecalls(uow, kdpExamResultTo.ExaminationCode, kdpExamResultTo.ClientId);

                uow.Commit();
            }
        }
        private void InsertKdpExaminationResult(IUnitOfWork uow, KdpExaminationResultTO kdpExamResultTo)
        {
            kdpExamResultTo.PkChildExaminationId = GetChildExaminationPrimaryKey(uow);

            uow.InsertTransferObject<KdpExaminationResultTO, ChildExamination>(kdpExamResultTo);
            uow.InsertTransferObject<KdpExaminationResultTO, ChildExaminationGiven>(kdpExamResultTo);
            uow.InsertTransferObject<KdpExaminationResultTO, ChildExaminationKdp>(kdpExamResultTo);


            if ((kdpExamResultTo.Height.HasValue || kdpExamResultTo.Weight.HasValue || kdpExamResultTo.HeadCircumference.HasValue) && kdpExamResultTo.ChildMeasurementId <= 0)
            {
                kdpExamResultTo.ChildMeasurementId = GetNextChildMeasurementPrimaryKey(uow);
                uow.InsertTransferObject<KdpExaminationResultTO, ChildMeasurement>(kdpExamResultTo);
            }
        }
        private static long GetChildExaminationPrimaryKey(IUnitOfWork uow)
        {
            return uow.GetNextId<ChildExamination>();
        }
        private static long GetNextChildMeasurementPrimaryKey(IUnitOfWork uow)
        {
            return uow.GetNextId<ChildMeasurement>();
        }
        public Tuple<double, double> GetAgeRangeFromExamSchedule(string examCode)
        {
            using (var uow = unitOfWorkFactory())
            {
                var scheduledExam = uow.Repository<PreschoolScheduleExams>()
                                        .WhereIsActive()
                                        .Where(x => x.FkExamCode == examCode)
                                        .Select(x => new { MinimumAgeWks = x.MinimumAgeWks, MaximumAgeWks = x.MaximumAgeWks })
                                        .FirstOrDefault();

                if (scheduledExam == null)
                    return null;

                var minimumAgeInWeeks = Convert.ToDouble(scheduledExam.MinimumAgeWks);
                var maximumAgeInWeeks = (double?)scheduledExam.MaximumAgeWks ?? double.MaxValue;

                return new Tuple<double,double>(minimumAgeInWeeks, maximumAgeInWeeks);
            }
        }
private static List<ChildExaminationGivenSubTO> GetKdpOutstandingAppointments(long p,IUnitOfWork u) => new();
private void UpdateKdpExaminationResult(IUnitOfWork u,KdpExaminationResultTO t,ChildExamination c) => throw new NotSupportedException("Editing excluded");
public void DeleteKdpExaminationResult(long i,long p,string c) => throw new NotSupportedException("Deletion excluded");
}}
