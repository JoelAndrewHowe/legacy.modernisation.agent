using Orvex.Business;
using Orvex.Business.Validation;
using Orvex.Services;
using Orvex.TransferObjects;

using Hcwp.Domain;

namespace Hcwp.Application;

// A narrow application boundary around the approved rules. No browser-supplied
// patient identity, edit ID, other contact, appointment or recall operation enters it.
public sealed class Kd03Recording
{
    private readonly IKdpExaminationService service;
    public Kd03Recording(Store store)
    {
        service = new KdpExaminationService(() => new UnitOfWork(store), new KdpExaminationValidator());
    }

    public KdpExaminationTO ReadPatient(long selectedPatient) => service.GetKdpExamination(selectedPatient);

    public KdpExaminationResultTO Add(long selectedPatient, KdpExaminationResultTO draft)
    {
        Kd03Scope.EnsureNewResult(selectedPatient, draft);
        var patient = ReadPatient(selectedPatient);
        service.SaveKdpExaminationResult(patient, draft);
        // The service factory opens a new EF context for this read, after disposal
        // of the write context. Do not return the submitted object.
        return service.GetKdpExaminationResult(draft.PkChildExaminationId);
    }
}
