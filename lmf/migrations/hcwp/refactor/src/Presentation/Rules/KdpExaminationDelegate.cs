// Extracted bundle file 5; see extract.py and README.md.
using System;
using System.Collections.Generic;
using System.Linq;
using System.ServiceModel;
using HLX.BusinessTier.Common.Util;
using HLX.Net2008.Common;
using Orvex.Business.Validation;
using Orvex.Messages;
using Orvex.Messages.Faults;
using Orvex.Services;
using Orvex.Services.Internal;
using Orvex.TransferObjects;

namespace Orvex.ViewModels
{
    public class KdpExaminationDelegate
    {
        private List<KdpExaminationResultDelegate> listOfKdpExaminationResultDelegates;
        private KdpExaminationTO ato;
        private readonly IKdpExaminationService service;
        private readonly KdpExaminationValidator validator;
        private readonly IMessenger messenger;
        private readonly Func<KdpExaminationResultDelegate> resultDelegateFactory;

        public decimal ChangesCount { get { return listOfKdpExaminationResultDelegates.Sum(rd => rd.ChangesCount); } }
        
        public List<KdpExaminationResultDelegate> KdpExaminationResultDelegates => listOfKdpExaminationResultDelegates;

        public KdpExaminationDelegate(IKdpExaminationService service, KdpExaminationValidator validator, IMessenger messenger, Func<KdpExaminationResultDelegate> resultDelegateFactory)
        {
            this.service = service;
            this.validator = validator;
            this.messenger = messenger;
            this.resultDelegateFactory = resultDelegateFactory;
        }

        public void GetKdpResults(long clientId)
        {
            ato = service.GetKdpExamination(clientId);
            listOfKdpExaminationResultDelegates = ato.HcpExaminationResultToList.OrderByDescending(it => it.ExaminationDate).Select(GetNewKdpExaminationResultDelegate).ToList();
        }

        public KdpExaminationResultDelegate AddNewKdpResult()
        {
            try
            {
                validator.ValidateKdpConsent(Convert.ToInt64(ato.Id), ato.HasPreschoolConsent);
            }
            catch (FaultException<ValidationWarningFault> ex)
            {
                var warning = new WarningNotificationMessage(ex.Message, Resources.Resources.KdpResultsTitle, ex.Detail.Title);
                messenger.Send(warning);
            }

            var newResult = new KdpExaminationResultTO
            {
                ClientId = Convert.ToInt64(ato.Id),
                PkChildExaminationId = 0,
                ResultEnteredDate = ReferenceClock.Now,
                Origin = (byte?)LookupsUtility.EXAMINATION_ORIGIN.UNSCHEDULED,
                Reschedule = HLXBoolean.False,
                HeightMeasurementDeclined = HLXBoolean.False,
                WeightMeasurementDeclined = HLXBoolean.False,
                HeadMeasurementDeclined = HLXBoolean.False,
                EnabledPropChangeEvents = true
            };

            

            foreach (var outstandingAppointment in ato.OutstandingAppointmentsList)
            {
                if (outstandingAppointment.ExaminationDate != null)
                {
                    var confirmationMessage = new YesNoConfirmationRequiredMessage(
                        string.Format(Resources.Resources.OutstandingAppointmentMessage,
                            outstandingAppointment.ExaminationCode, outstandingAppointment.ExaminationDate.Value.ToString("dd MMM yyyy")),
                        Resources.Resources.KdpResultsTitle, Resources.Resources.OutstandingAppointmentExistsPrompt);
                    messenger.Send(confirmationMessage);

                    if (confirmationMessage.Response)
                    {
                        newResult.ExaminationCode = outstandingAppointment.ExaminationCode;
                        newResult.ExaminationDate = outstandingAppointment.ExaminationDate.Value;
                        newResult.Origin = (byte?)outstandingAppointment.Origin;
                        break;
                    }
                }
            }

            var newResultDelegate = GetNewKdpExaminationResultDelegate(newResult);

            listOfKdpExaminationResultDelegates.Insert(0,newResultDelegate);
            return newResultDelegate;
        }
      
        private KdpExaminationResultDelegate GetNewKdpExaminationResultDelegate(KdpExaminationResultTO kdpExaminationResultTo)
        {
            var kdpResultDelegate = resultDelegateFactory();
            kdpResultDelegate.Populate(kdpExaminationResultTo, ato.Gender, ato.DateOfBirth, ato.DateOfDeath, ato.HcpExaminationResultToList);
            return kdpResultDelegate;
        }

        public bool Save(long kdpChildExaminationId)
        {
            try
            {
                var kdpExamResultToSave =
                    listOfKdpExaminationResultDelegates.Single(re => re.PkChildExaminationId == kdpChildExaminationId)
                        .KdpExaminationResultTo;
                service.SaveKdpExaminationResult(ato, kdpExamResultToSave);
                return true;
            }
            catch (FaultException<OptimisticLockFault> ex)
            {
                var error = new NonFatalErrorEncountered(ex.Message, Resources.Resources.KdpResultsTitle, Resources.Resources.ExamResultsErrorSavingPrompt);
                messenger.Send(error);
                return false;
            }
            catch (FaultException ex)
            {
                var error = new NonFatalErrorEncountered(ex.Message, Resources.Resources.KdpResultsTitle, Resources.Resources.ExamResultsErrorSavingPrompt);
                messenger.Send(error);
                return false;
            }
        }

        public bool ConfirmCancelChanges(long kdpChildExaminationId)
        {
            if (KdpExaminationResultDelegates.Count >0 && kdpChildExaminationId >0)
            {
                var kdpExamResultDelegate = KdpExaminationResultDelegates.Single(er => er.PkChildExaminationId == kdpChildExaminationId);
                if (kdpExamResultDelegate != null && kdpExamResultDelegate.KdpExaminationResultTo.hasChanged())
                {
                    var confirmation = new YesNoConfirmationRequiredMessage(Resources.Resources.ExamResultsConfirmCancelMessage, Resources.Resources.KdpResultsTitle, Resources.Resources.ConfirmCancelPrompt);
                    messenger.Send(confirmation);
                    if (confirmation.Response)
                    {
                        kdpExamResultDelegate.KdpExaminationResultTo = service.GetKdpExaminationResult(kdpExamResultDelegate.KdpExaminationResultTo.PkChildExaminationId);
                        return true;
                    }
                    return false;
                }return true;
            }
            return true;
        }

        public bool Delete(long examinationId, long clientId, string examinationCode)
        {
            var confirmation = new YesNoConfirmationRequiredMessage(Resources.Resources.ConfirmContinue, Resources.Resources.KdpResultsTitle, Resources.Resources.ConfirmDeletionPrompt);
            messenger.Send(confirmation);

            if (!confirmation.Response)
                return false;

            if (examinationId > 0)
            {
                try
                {
                    service.DeleteKdpExaminationResult(examinationId, clientId, examinationCode);
                }
                catch (FaultException<OptimisticLockFault>)
                {
                    messenger.Send(new WarningNotificationMessage(Resources.Resources.OptimisticLockOnDeleteMessage, Resources.Resources.KdpResultsTitle, Resources.Resources.WarningPrompt));
                }
                catch (FaultException ex)
                {
                    messenger.Send(new NonFatalErrorEncountered(ex.Message, Resources.Resources.KdpResultsTitle, Resources.Resources.ExamResultsErrorDeletingPrompt));
                    return false;
                }
            }

            return true;
        }
    }
}
