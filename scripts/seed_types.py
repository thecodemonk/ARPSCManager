from app import create_app
from app.extensions import db
from app.models import EquipmentType, TrainingType
app = create_app('production')
with app.app_context():
    if EquipmentType.query.count() == 0:
        for name, has_details, order in [('HF Radio', False, 1), ('Dual-Band Radio', True, 2), ('Digital / Winlink', False, 3), ('Backup Power', True, 4), ('Field Deployable', False, 5)]:
            db.session.add(EquipmentType(name=name, has_details=has_details, display_order=order))
    if TrainingType.query.count() == 0:
        for name, has_exp, exp_years, order in [('IS-100', False, None, 1), ('IS-200', False, None, 2), ('IS-700', False, None, 3), ('IS-800', False, None, 4), ('ICS-300', False, None, 5), ('ICS-400', False, None, 6), ('EC-001', False, None, 7), ('EC-016', False, None, 8), ('AUXCOMM', False, None, 9), ('SKYWARN', True, 2, 10)]:
            db.session.add(TrainingType(name=name, has_expiration=has_exp, expiration_years=exp_years, display_order=order))
    db.session.commit()
    print('Seeded.')
