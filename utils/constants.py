APPOINTMENT_REASONS = {
    "System Checkup",
    "Irrigation Design",
    "Piping Installation",
    "Pump Maintenance",
    "Drippers Setup",
    "Filter Cleaning",
    "System Optimization",
    "Urgent Leak Repair"
}


PATIENT_GENDERS = {
    "Male",
    "Female",
}


from utils.settings_helper import get_treatment_prices

class TreatmentPricesProxy(dict):
    def __getitem__(self, key):
        return get_treatment_prices()[key]
        
    def get(self, key, default=None):
        return get_treatment_prices().get(key, default)
        
    def keys(self):
        return get_treatment_prices().keys()
        
    def items(self):
        return get_treatment_prices().items()
        
    def values(self):
        return get_treatment_prices().values()
        
    def __contains__(self, key):
        return key in get_treatment_prices()
        
    def __iter__(self):
        return iter(get_treatment_prices())

    def __len__(self):
        return len(get_treatment_prices())

    def __repr__(self):
        return repr(get_treatment_prices())


class TreatmentProcedureTypesProxy(set):
    def __contains__(self, item):
        return item in get_treatment_prices()
        
    def __iter__(self):
        return iter(get_treatment_prices().keys())

    def __len__(self):
        return len(get_treatment_prices())

    def __repr__(self):
        return repr(set(get_treatment_prices().keys()))


TREATMENT_PRICES = TreatmentPricesProxy()
TREATMENT_PROCEDURE_TYPES = TreatmentProcedureTypesProxy()