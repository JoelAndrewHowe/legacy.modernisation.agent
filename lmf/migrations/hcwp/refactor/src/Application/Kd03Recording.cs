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
    private readonly Store store;
    public Kd03Recording(Store store)
    {
        this.store = store;
        service = new KdpExaminationService(() => new UnitOfWork(store), new KdpExaminationValidator());
    }

    public Orvex.ViewModels.KdpExaminationDelegate CreateRules(Orvex.Services.Internal.IMessenger messenger, ILookupService lookups)
    {
        var validator = new KdpExaminationValidator();
        return new(service, validator, messenger, () => new Orvex.ViewModels.KdpExaminationResultDelegate(
            validator, messenger, lookups, new Orvex.Business.ChildMeasurementsService(() => new UnitOfWork(store)), service));
    }

    public KdpExaminationTO ReadPatient(long selectedPatient) => service.GetKdpExamination(selectedPatient);

    // Read-only query adapter: an unavailable selected-patient context has no
    // visible results. Keep recording's approved missing-patient behaviour intact.
    public IReadOnlyList<KdpExaminationResultTO> ReadResults(long selectedPatient)
    {
        using (var uow = new UnitOfWork(store))
        {
            if (!uow.Repository<Orvex.Model.ChildGeneral>().Any(p => p.ClientId == selectedPatient))
                return Array.Empty<KdpExaminationResultTO>();
        }
        return ReadPatient(selectedPatient).HcpExaminationResultToList.ToList().AsReadOnly();
    }

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
