import re

translations = {
    "Sun": "الأحد",
    "Mon": "الاثنين",
    "No Patients Found": "لم يتم العثور على مرضى",
    "You need to add at least one patient to the database before you can schedule an appointment.": "يجب عليك إضافة مريض واحد على الأقل إلى قاعدة البيانات لتتمكن من جدولة موعد.",
    "Tue": "الثلاثاء",
    "Wed": "الأربعاء",
    "Thu": "الخميس",
    "Fri": "الجمعة",
    "Sat": "السبت",
    "Sat - Thu": "السبت - الخميس",
    "Sun - Thu": "الأحد - الخميس",
    "Mon - Fri": "الاثنين - الجمعة",
    "Mon - Sat": "الاثنين - السبت",
    "Every day": "كل يوم",
    "AM": "ص",
    "PM": "م",
    "Clinic Closed": "العيادة مغلقة",
    "Appointments cannot be booked on holidays (Clinic is closed).": "لا يمكن حجز المواعيد في العطل الرسمية (العيادة مغلقة).",
    "Invalid Date": "التاريخ غير صالح",
    "Appointments cannot be booked in the past.": "لا يمكن حجز مواعيد في الماضي.",
    "Invalid Time": "الوقت غير صالح",
    "Selected time is in the past. Please choose a future time.": "الوقت المحدد في الماضي. يرجى اختيار وقت مستقبلي.",
    "Outside Business Hours": "خارج أوقات العمل",
    "Booking Period Exceeded": "تجاوزت فترة الحجز",
    "Appointments cannot be booked more than 30 days in advance.": "لا يمكن حجز المواعيد قبل أكثر من 30 يوماً.",
    "Clinic Closing Soon": "ستغلق العيادة قريباً",
    "There are no remaining booking slots for today. Please select a future date.": "لا توجد فتحات حجز متبقية لليوم. يرجى اختيار تاريخ مستقبلي.",
    "Creating Appointment...": "جاري إنشاء الموعد...",
    "Redirecting to appointment form": "جاري التوجيه إلى نموذج الموعد",
    "Month": "الشهر",
    "Week": "الأسبوع",
    "List": "قائمة",
    "Today": "اليوم",
    "Appointments must be scheduled between": "يجب جدولة المواعيد بين",
    "and": "و",
    "% Completed": "نسبة الإنجاز",
    "(leave blank to keep current)": "(اتركه فارغاً للاحتفاظ بالمعلومات الحالية)",
    "15 Minutes": "15 دقيقة",
    "30 Minutes": "30 دقيقة",
    "30-Day Booking Window": "نافذة حجز 30 يوماً",
    "45 Minutes": "45 دقيقة",
    "60 Minutes": "60 دقيقة",
    "Action": "الإجراء",
    "Actions": "الإجراءات",
    "Add Appointment": "إضافة موعد",
    "Add First Appointment": "إضافة الموعد الأول",
    "Add First Treatment": "إضافة المعالجة الأولى",
    "Add Invoice": "إضافة فاتورة",
    "Add Item": "إضافة بند",
    "Add Manual Invoice": "إضافة فاتورة يدوية",
    "Add New Appointment": "إضافة موعد جديد",
    "Add New Patient": "إضافة مريض جديد",
    "Add New Payment": "إضافة دفعة جديدة",
    "Add New Procedure": "إضافة إجراء جديد",
    "Add New Treatment": "إضافة معالجة جديدة",
    "Add New User": "إضافة مستخدم جديد",
    "Add Patient": "إضافة مريض",
    "Add Payment": "إضافة دفعة",
    "Add Treatment": "إضافة معالجة",
    "Add a treatment record for this appointment session": "إضافة سجل معالجة لجلسة الموعد هذه",
    "Add any medical information about the patient": "إضافة أي معلومات طبية عن المريض",
    "Add any notes about the patient": "إضافة أي ملاحظات عن المريض",
    "Add any notes about the patient's appointment": "إضافة أي ملاحظات حول موعد المريض",
    "Add one or more procedures to this invoice": "إضافة إجراء أو أكثر لهذه الفاتورة",
    "Add treatment notes": "إضافة ملاحظات المعالجة",
    "Address": "العنوان",
    "Admin": "مدير",
    "All Statuses": "جميع الحالات",
    "All appointments related to this patient": "جميع المواعيد المتعلقة بهذا المريض",
    "All clear! No patients have outstanding balances": "كل شيء تمام! لا يوجد ديون مستحقة على أي مريض",
    "All invoices are fully paid": "جميع الفواتير مدفوعة بالكامل",
    "All invoices generated from appointments with treatments": "جميع الفواتير التي تم إنشاؤها من المواعيد مع المعالجات",
    "All patient payments recorded in the clinic": "جميع مدفوعات المرضى المسجلة في العيادة",
    "All payments recorded for this patient": "جميع المدفوعات المسجلة لهذا المريض",
    "All previous treatments recorded for this patient, ordered from newest to oldest": "جميع المعالجات السابقة المسجلة لهذا المريض، مرتبة من الأحدث إلى الأقدم",
    "All recorded treatments across this patient's appointments": "جميع المعالجات المسجلة عبر مواعيد هذا المريض",
    "All rights reserved": "جميع الحقوق محفوظة",
    "All treatments recorded during this appointment session": "جميع المعالجات المسجلة خلال جلسة الموعد هذه",
    "Allocated": "مخصص",
    "Allocated Amount": "المبلغ المخصص",
    "Amount": "المبلغ",
    "Apply": "تطبيق",
    "Apply Filter": "تطبيق الفلتر",
    "Apply Search": "تطبيق البحث",
    "Appointment": "الموعد",
    "Appointment Calendar": "تقويم المواعيد",
    "Appointment Date": "تاريخ الموعد",
    "Appointment Date & Time": "تاريخ ووقت الموعد",
    "Appointment Details": "تفاصيل الموعد",
    "Appointment Notes": "ملاحظات الموعد",
    "Appointment Reason": "سبب الموعد",
    "Appointment Session": "جلسة الموعد",
    "Appointment Sessions": "جلسات المواعيد",
    "Appointment Status": "حالة الموعد",
    "Appointment Statuses": "حالات المواعيد",
    "Appointments": "المواعيد",
    "Appointments List": "قائمة المواعيد",
    "Appointments completed today with treatment and payment summary": "المواعيد المنجزة اليوم مع ملخص المعالجة والدفع",
    "Appointments scheduled for today and still waiting to be completed": "المواعيد المجدولة لليوم وما زالت بانتظار الإنجاز",
    "Are you sure you want to permanently delete this appointment?": "هل أنت متأكد من رغبتك في حذف هذا الموعد نهائياً؟",
    "Are you sure you want to permanently delete this patient?": "هل أنت متأكد من رغبتك في حذف هذا المريض نهائياً؟",
    "Are you sure you want to permanently delete this treatment?": "هل أنت متأكد من رغبتك في حذف هذه المعالجة نهائياً؟",
    "Back": "رجوع",
    "Back to Appointments": "العودة إلى المواعيد",
    "Back to Home": "العودة إلى الرئيسية",
    "Back to Invoices": "العودة إلى الفواتير",
    "Back to Patient": "العودة إلى المريض",
    "Back to Session": "العودة إلى الجلسة",
    "Billing & Finance": "الفوترة والمالية",
    "Billing & Finance Settings": "إعدادات الفوترة والمالية",
    "Braces / Orthodontics": "تقويم الأسنان",
    "Built for professional clinic management": "مبني للإدارة الاحترافية للعيادات",
    "Calendar": "التقويم",
    "Calendar & Appointment Settings": "إعدادات التقويم والمواعيد",
    "Calendar Settings": "إعدادات التقويم",
    "Cancel": "إلغاء",
    "Cancelled": "ملغى",
    "Cancelled appointment — treatments cannot be added": "موعد ملغى — لا يمكن إضافة معالجات",
    "Check-up": "فحص دوري",
    "Checked days represent active business days. Unchecked days will be styled as weekends/closed days in the interactive calendar and will prevent scheduling appointments": "تمثل الأيام المحددة أيام العمل الفعلية. الأيام غير المحددة ستظهر كعطلة نهاية أسبوع/مغلق في التقويم التفاعلي وتمنع جدولة المواعيد",
    "Checking status": "تحقق من الحالة",
    "Choose whether the patient paid now or not": "اختر ما إذا كان المريض قد سدد المبلغ الآن أم لا",
    "City": "المدينة",
    "Cleaning": "تنظيف وتلميع",
    "Click any appointment to view details and manage the session": "انقر على أي موعد لعرض التفاصيل وإدارة الجلسة",
    "Clinic Activity": "نشاط العيادة",
    "Clinic Credit": "رصيد العيادة",
    "Clinic Info": "معلومات العيادة",
    "Clinic Staff": "الكادر الطبي",
    "Staff Sign In": "دخول الكادر",
    "Patient Sign In": "دخول المرضى",
    "Clinic Management System Portal": "بوابة نظام إدارة العيادة",
    "Clinic Name": "اسم العيادة",
    "Clinic Overview": "نظرة عامة على العيادة",
    "Clinic Profile": "ملف العيادة",
    "Clinic Tools": "أدوات العيادة",
    "Closed": "مغلق",
    "Closed session — read-only mode": "جلسة مغلقة — وضع القراءة فقط",
    "Complete overview of the patient's profile, appointments, treatments, and financial summary": "عرض كامل لملف المريض ومواعيده ومعالجاته والملخص المالي",
    "Completed": "منجز",
    "Completed Today": "منجز اليوم",
    "Completed appointment sessions will appear here after using End Session": "تظهر جلسات المواعيد المكتملة هنا بعد إنهاء الجلسة",
    "Comprehensive financial and operational analysis for your clinic": "تحليل مالي وتشغيلي شامل لعيادتك",
    "Configure working hours and default durations": "تكوين ساعات العمل والمدد الافتراضية",
    "Country": "البلد",
    "Create Account": "إنشاء حساب",
    "Create Invoice": "إنشاء فاتورة",
    "Create User Account": "إنشاء حساب مستخدم",
    "Create a walk-in invoice with one or more treatment items": "إنشاء فاتورة مباشرة مع بند معالجة واحد أو أكثر",
    "Credit": "رصيد",
    "Crown / Bridge": "تاج / جسر",
    "Custom Amount": "مبلغ مخصص",
    "Custom Currency Symbol": "رمز العملة المخصص",
    "Custom Payment Amount": "مبلغ دفعة مخصص",
    "Customize clinic profile, working hours, billing details, and treatment prices": "تخصيص ملف العيادة وساعات العمل وتفاصيل الفواتير وأسعار المعالجات",
    "Customize the visual theme of the application": "تخصيص المظهر المرئي للتطبيق",
    "Daily Working Hours End": "ساعة نهاية العمل اليومي",
    "Daily Working Hours Start": "ساعة بداية العمل اليومي",
    "Dark Mode": "الوضع الداكن",
    "Dashboard": "لوحة التحكم",
    "Date": "التاريخ",
    "Date & Time": "التاريخ والوقت",
    "Date Of Appointment": "تاريخ الموعد",
    "Date Of Birth": "تاريخ الميلاد",
    "Date of Birth": "تاريخ الميلاد",
    "Default Price": "السعر الافتراضي",
    "Default Session Duration": "المدة الافتراضية للجلسة",
    "Delete All Cancelled": "حذف جميع المواعيد الملغاة",
    "Delete Appointment": "حذف الموعد",
    "Delete Patient": "حذف المريض",
    "Delete Treatment": "حذف المعالجة",
    "Dental Clinic MS": "نظام إدارة عيادة الأسنان",
    "Dental Clinic Management System for managing patients, appointments": "نظام إدارة عيادة الأسنان لإدارة المرضى والمواعيد",
    "Detailed invoice view with treatments, payments, and current invoice status": "عرض تفصيلي للفاتورة مع المعالجات والمدفوعات وحالة الفاتورة الحالية",
    "Discount": "الخصم",
    "Discount (%)": "الخصم (%)",
    "Doctor": "طبيب",
    "Done": "منجز",
    "Done Appointments": "المواعيد المنجزة",
    "Done Today": "منجز اليوم",
    "Dr": "د.",
    "Due": "مستحق",
    "Edit": "تعديل",
    "Edit Appointment": "تعديل الموعد",
    "Edit Discount": "تعديل الخصم",
    "Edit Patient": "تعديل المريض",
    "Edit Treatment": "تعديل المعالجة",
    "Edit User Account": "تعديل حساب المستخدم",
    "Email": "البريد الإلكتروني",
    "Email Address": "عنوان البريد الإلكتروني",
    "Emergency Contact": "جهة اتصال الطوارئ",
    "Emergency Pain": "ألم طارئ",
    "End Session": "إنهاء الجلسة",
    "English": "English (الإنجليزية)",
    "Enter address": "أدخل العنوان",
    "Enter amount": "أدخل المبلغ",
    "Enter city": "أدخل المدينة",
    "Enter country": "أدخل البلد",
    "Enter email address": "أدخل البريد الإلكتروني",
    "Enter emergency contact": "أدخل جهة اتصال الطوارئ",
    "Enter first name": "أدخل الاسم الأول",
    "Enter last name": "أدخل اسم العائلة",
    "Enter medicare number": "أدخل رقم الرعاية الصحية",
    "Enter new password (optional)": "أدخل كلمة مرور جديدة (اختياري)",
    "Enter occupation": "أدخل المهنة",
    "Enter password": "أدخل كلمة المرور",
    "Enter payment amount": "أدخل مبلغ الدفعة",
    "Enter phone number": "أدخل رقم الهاتف",
    "Enter post code": "أدخل الرمز البريدي",
    "Enter preferred first name": "أدخل الاسم الأول المفضل",
    "Enter state": "أدخل الولاية / المحافظة",
    "Enter username": "أدخل اسم المستخدم",
    "Enter your password": "أدخل كلمة المرور",
    "Enter your username": "أدخل اسم المستخدم",
    "Example: 14": "مثال: 14",
    "Expected Status": "الحالة المتوقعة",
    "Extraction": "قلع سن",
    "Facebook": "فيسبوك",
    "Female": "أنثى",
    "Fill in the appointment information to create a new record": "املأ معلومات الموعد لإنشاء سجل جديد",
    "Fill in the patient information to create a new record": "املأ معلومات المريض لإنشاء سجل جديد",
    "Filling": "حشوة أسنان",
    "Finance Load": "العبء المالي",
    "Financial Summary": "الملخص المالي",
    "First Name": "الاسم الأول",
    "First name": "الاسم الأول",
    "Follow up with patients having outstanding dental invoices": "متابعة المرضى الذين لديهم فواتير أسنان مستحقة",
    "Follow-up": "متابعة",
    "Friday": "الجمعة",
    "Full Name": "الاسم الكامل",
    "Full Payment": "دفعة كاملة",
    "Full Price": "السعر الكامل",
    "Gender": "الجنس",
    "Generated from appointment treatments": "تم إنشاؤها من معالجات المواعيد",
    "Here's a list of your latest appointments": "إليك قائمة بآخر مواعيدك",
    "Here's a list of your latest patients": "إليك قائمة بآخر مرضاك",
    "HomePage": "الصفحة الرئيسية",
    "ID": "المعرف",
    "Instagram": "إنستغرام",
    "Interactive Calendar": "التقويم التفاعلي",
    "Invoice": "الفاتورة",
    "Invoice #": "فاتورة رقم #",
    "Invoice Details": "تفاصيل الفاتورة",
    "Invoice Items": "بنود الفاتورة",
    "Invoice Number": "رقم الفاتورة",
    "Invoice Status": "حالة الفاتورة",
    "Invoice Total": "إجمالي الفاتورة",
    "Invoice number, patient name, phone, appointment status": "رقم الفاتورة، اسم المريض، الهاتف، حالة الموعد",
    "Invoiced": "مفوتر",
    "Invoices": "الفواتير",
    "Invoices List": "قائمة الفواتير",
    "Invoices will appear here when an appointment has at least one treatment": "ستظهر الفواتير هنا عندما يحتوي الموعد على معالجة واحدة على الأقل",
    "Last Name": "الاسم الأخير",
    "Last name": "الاسم الأخير",
    "Light Mode": "الوضع الفاتح",
    "LinkedIn": "لينكد إن",
    "Logged in": "تسجيل الدخول كـ",
    "Login": "تسجيل الدخول",
    "Logout": "تسجيل الخروج",
    "Male": "ذكر",
    "Manage Patients": "إدارة المرضى",
    "Manage all appointments from one place": "إدارة جميع المواعيد من مكان واحد",
    "Manage all clinic payments from one place": "إدارة جميع مدفوعات العيادة من مكان واحد",
    "Manage all patients from one place": "إدارة جميع المرضى من مكان واحد",
    "Manage procedure types and their default pricing": "إدارة أنواع الإجراءات وأسعارها الافتراضية",
    "Manage system users, roles, and credentials": "إدارة مستخدمي النظام وأدوارهم وصلاحياتهم",
    "Manage treatments related to this appointment session": "إدارة المعالجات المتعلقة بجلسة الموعد هذه",
    "Manual": "يدوي",
    "Manual / Walk-in Invoice": "فاتورة يدوية / مباشرة",
    "Medical Information": "المعلومات الطبية",
    "Medicare Number": "رقم الرعاية الصحية",
    "Miss": "آنسة",
    "Monday": "الاثنين",
    "Monthly Financial Performance (Last 6 Months)": "الأداء المالي الشهري (آخر 6 أشهر)",
    "Mr": "السيد",
    "Mrs": "السيدة",
    "Ms": "الآنسة",
    "N/A": "غير متوفر",
    "Name, phone, email, or city": "الاسم، الهاتف، البريد الإلكتروني، أو المدينة",
    "New Appointment": "موعد جديد",
    "New Password": "كلمة مرور جديدة",
    "New Patient": "مريض جديد",
    "Next": "التالي",
    "Next Upcoming Appointment": "الموعد القادم التالي",
    "No Credit": "لا يوجد رصيد",
    "No Payment": "لا يوجد دفع",
    "No appointments found": "لم يتم العثور على مواعيد",
    "No appointments match your current filters": "لا توجد مواعيد تطابق الفلاتر الحالية",
    "No appointments yet": "لا توجد مواعيد بعد",
    "No completed appointments today": "لا توجد مواعيد مكتملة اليوم",
    "No invoices found": "لم يتم العثور على فواتير",
    "No invoices match your search": "لا توجد فواتير تطابق بحثك",
    "No more upcoming appointments scheduled for today": "لا توجد مواعيد قادمة مجدولة اليوم",
    "No notes available": "لا تتوفر ملاحظات",
    "No patients found": "لم يتم العثور على مرضى",
    "No patients match your current search": "لا يوجد مرضى يطابقون بحثك الحالي",
    "No payments found": "لم يتم العثور على مدفوعات",
    "No payments match your search": "لا توجد مدفوعات تطابق بحثك",
    "No payments yet": "لا توجد مدفوعات بعد",
    "No previous treatments": "لا توجد معالجات سابقة",
    "No scheduled appointments today": "لا توجد مواعيد مجدولة اليوم",
    "No treatments recorded yet": "لم يتم تسجيل معالجات بعد",
    "No treatments yet": "لا توجد معالجات بعد",
    "Notes": "الملاحظات",
    "Occupation": "المهنة",
    "Open Patient": "فتح ملف المريض",
    "Open Session": "فتح الجلسة",
    "Open Treatment Session": "فتح جلسة معالجة",
    "Open session — treatments can be added or modified": "جلسة مفتوحة — يمكن إضافة المعالجات أو تعديلها",
    "Operating Hours": "ساعات العمل",
    "Optional notes about this payment": "ملاحظات اختيارية حول هذه الدفعة",
    "Outstanding": "مستحق",
    "Outstanding / Credit": "مستحق / رصيد",
    "Outstanding Amount": "المبلغ المستحق",
    "Outstanding Balance": "الرصيد المستحق",
    "Outstanding Balances": "الأرصدة المستحقة",
    "Outstanding Debt": "الديون المستحقة",
    "PAY": "سداد",
    "Paid": "مدفوع",
    "Paid Ratio": "نسبة المدفوع",
    "Partial": "جزئي",
    "Password": "كلمة المرور",
    "Patient": "المريض",
    "Patient Credit": "رصيد المريض",
    "Patient Details": "تفاصيل المريض",
    "Patient Gender Demographics": "الديموغرافيا الجنسية للمرضى",
    "Patient Name": "اسم المريض",
    "Patient Payments": "مدفوعات المريض",
    "Patient Phone": "هاتف المريض",
    "Patient name": "اسم المريض",
    "Patients": "المرضى",
    "Patients List": "قائمة المرضى",
    "Payment": "الدفعة",
    "Payment #": "دفعة رقم #",
    "Payment Allocations": "تخصيصات الدفع",
    "Payment Amount": "مبلغ الدفعة",
    "Payment Date": "تاريخ الدفع",
    "Payment Notes": "ملاحظات الدفع",
    "Payment Option": "خيارات الدفع",
    "Payments": "المدفوعات",
    "Payments List": "قائمة المدفوعات",
    "Payments allocated to this invoice": "المدفوعات المخصصة لهذه الفاتورة",
    "Payments will appear here after they are recorded for patients": "ستظهر المدفوعات هنا بعد تسجيلها للمرضى",
    "Phone": "الهاتف",
    "Phone Number": "رقم الهاتف",
    "Post Code": "الرمز البريدي",
    "Preferred First Name": "الاسم الأول المفضل",
    "Previous": "السابق",
    "Previous Treatments": "المعالجات السابقة",
    "Price": "السعر",
    "Procedure Name": "اسم الإجراء",
    "Procedure Price": "سعر الإجراء",
    "Procedure Type": "نوع الإجراء",
    "Quick Access": "وصول سريع",
    "Quick Cancel": "إلغاء سريع",
    "Quick Complete": "إنجاز سريع",
    "Quick overview of this patient's financial balance": "نظرة عامة سريعة على الرصيد المالي للمريض",
    "Realtime operational metrics": "مؤشرات التشغيل الفورية",
    "Reason": "السبب",
    "Receptionist": "موظف استقبال",
    "Record a payment on the patient profile. The system will apply it to the oldest unpaid": "تسجيل دفعة في ملف المريض الشخصي. سيقوم النظام بتطبيقها تلقائياً على الفواتير الأقدم غير المدفوعة",
    "Remove": "إزالة",
    "Reopen Session": "إعادة فتح الجلسة",
    "Reports": "التقارير",
    "Reports & Statistics": "التقارير والإحصائيات",
    "Reports Dashboard": "لوحة التقارير",
    "Reset": "إعادة تعيين",
    "Reset Search": "إعادة تعيين البحث",
    "Revenue": "الإيرادات",
    "Review invoice totals, payments, and outstanding balances": "مراجعة إجماليات الفواتير والمدفوعات والأرصدة المستحقة",
    "Role": "الدور",
    "Root Canal": "علاج عصب السن",
    "Saturday": "السبت",
    "Save All Settings": "حفظ جميع الإعدادات",
    "Save Appointment": "حفظ الموعد",
    "Save Changes": "حفظ التغييرات",
    "Save Patient": "حفظ بيانات المريض",
    "Save Payment": "حفظ الدفعة",
    "Save Treatment": "حفظ المعالجة",
    "Scheduled": "مجدول",
    "Scheduled Appointments": "المواعيد المجدولة",
    "Scheduled Today": "مجدول اليوم",
    "Search": "بحث",
    "Search Invoice": "بحث عن فاتورة",
    "Search Patient": "البحث عن مريض",
    "Search Payments": "البحث عن المدفوعات",
    "Search by patient, phone, payment number, date, amount, or notes": "ابحث باسم المريض، الهاتف، رقم الدفعة، التاريخ، المبلغ، أو الملاحظات",
    "Select Gender": "اختر الجنس",
    "Select Patient": "اختر المريض",
    "Select a Patient": "اختر مريضاً",
    "Select a Procedure Type": "اختر نوع الإجراء",
    "Select a Reason": "اختر السبب",
    "Select a Status": "اختر الحالة",
    "Select a Title": "اختر اللقب",
    "Select a procedure type to show price": "اختر نوع الإجراء لعرض السعر",
    "Select patient": "اختر المريض",
    "Select procedure": "اختر الإجراء",
    "Selected Payment": "الدفعة المحددة",
    "Session Mode": "وضع الجلسة",
    "Session Status": "حالة الجلسة",
    "Session Treatments": "معالجات الجلسة",
    "Set the currency symbol used across invoices and reports": "تحديد رمز العملة المستخدم في الفواتير والتقارير",
    "Settings": "الإعدادات",
    "Sign In": "تسجيل الدخول",
    "Start Session": "بدء الجلسة",
    "State": "الولاية / المحافظة",
    "Status": "الحالة",
    "Subtotal": "المجموع الفرعي",
    "Sunday": "الأحد",
    "System Display Theme": "مظهر عرض النظام",
    "System Interface Language": "لغة واجهة النظام",
    "System Role": "دور النظام",
    "System Settings": "إعدادات النظام",
    "Theme & Appearance": "المظهر والثيم",
    "There are no appointments yet": "لا توجد مواعيد بعد",
    "There are no patients yet": "لا يوجد مرضى بعد",
    "There are no scheduled appointments waiting for today": "لا توجد مواعيد مجدولة بانتظار البدء اليوم",
    "This action cannot be undone": "هذا الإجراء لا يمكن التراجع عنه",
    "This appointment is cancelled. Appointment is read-only": "هذا الموعد ملغى. الموعد للقراءة فقط",
    "This appointment is cancelled. Treatment is read-only": "هذا الموعد ملغى. المعالجة للقراءة فقط",
    "This appointment is cancelled. Treatments cannot be added": "هذا الموعد ملغى. لا يمكن إضافة معالجات",
    "This appointment session is done. Appointment is read-only": "جلسة الموعد هذه منتهية. الموعد للقراءة فقط",
    "This appointment session is done. Treatment is read-only": "جلسة الموعد هذه منتهية. المعالجة للقراءة فقط",
    "This invoice has an outstanding balance": "هذه الفاتورة تحتوي على رصيد مستحق غير مدفوع",
    "This invoice has an overpayment credit": "هذه الفاتورة تحتوي على رصيد فائض مدفوع",
    "This invoice is fully paid": "هذه الفاتورة مدفوعة بالكامل",
    "This patient has an outstanding balance": "هذا المريض لديه رصيد مستحق غير مدفوع",
    "This patient has an overpayment credit": "هذا المريض لديه رصيد فائض مدفوع",
    "This patient has no appointments at the moment": "ليس لدى هذا المريض أي مواعيد في الوقت الحالي",
    "This patient has no recorded payments": "لم يتم تسجيل أي مدفوعات لهذا المريض",
    "This patient has no treatments from previous appointments": "ليس لدى هذا المريض أي معالجات من مواعيد سابقة",
    "This patient has no treatments yet. Treatments are added from appointment sessions": "ليس لدى هذا المريض أي معالجات بعد. يتم إضافة المعالجات من جلسات المواعيد",
    "This session is still open. You can add one or more treatments": "هذه الجلسة لا تزال مفتوحة. يمكنك إضافة معالجة واحدة أو أكثر",
    "This session was ended without recorded treatments": "تم إنهاء هذه الجلسة دون تسجيل أي معالجات",
    "This symbol will be applied dynamically to all invoices, payments, and report pages": "سيتم تطبيق هذا الرمز ديناميكياً على جميع الفواتير والمدفوعات وصفحات التقارير",
    "This will create a completed appointment, treatment items, and an invoice": "سيؤدي هذا إلى إنشاء موعد مكتمل وبنود معالجة وفاتورة",
    "Thursday": "الخميس",
    "Time": "الوقت",
    "Title": "اللقب",
    "Today's Paid": "المدفوع اليوم",
    "Today's Progress": "تقدم اليوم",
    "Today's Revenue": "إيرادات اليوم",
    "Today's Status": "حالة اليوم",
    "Today’s": "نظرة عامة على",
    "Today’s Scheduled Appointments": "مواعيد اليوم المجدولة",
    "Tooth": "السن",
    "Tooth Number": "رقم السن",
    "Tooth number": "رقم السن",
    "Top 5 Procedure Types (by Volume)": "أهم 5 معالجات (من حيث العدد)",
    "Top Patient Outstanding Balances": "أعلى أرصدة ديون مستحقة على المرضى",
    "Total Billed": "إجمالي الفواتير",
    "Total Invoiced": "إجمالي الفواتير",
    "Total Invoices": "إجمالي الفواتير",
    "Total Paid": "إجمالي المدفوعات",
    "Total Patients": "إجمالي المرضى",
    "Total Payments": "إجمالي المدفوعات",
    "Total Remaining": "الإجمالي المتبقي",
    "Total Treatments": "إجمالي المعالجات",
    "Track patients, appointments, treatments, payments, and outstanding balances": "تتبع المرضى والمواعيد والمعالجات والمدفوعات والأرصدة المستحقة",
    "Treatment Date": "تاريخ المعالجة",
    "Treatment Pricing": "أسعار المعالجات",
    "Treatment Services & Prices": "خدمات وأسعار المعالجات",
    "Treatments": "المعالجات",
    "Treatments included in this invoice": "المعالجات المشمولة في هذه الفاتورة",
    "Tuesday": "الثلاثاء",
    "Unknown appointment status": "حالة الموعد غير معروفة",
    "Unpaid": "غير مدفوع",
    "Update the appointment information": "تحديث معلومات الموعد",
    "Update the treatment information": "تحديث معلومات المعالجة",
    "Update your clinic's basic information": "تحديث المعلومات الأساسية لعيادتك",
    "User Accounts": "حسابات المستخدمين",
    "Username": "اسم المستخدم",
    "View Appointment": "عرض الموعد",
    "View Appointments": "عرض المواعيد",
    "View Detail": "عرض التفاصيل",
    "View Invoice": "عرض الفاتورة",
    "View Patient": "عرض ملف المريض",
    "View Patient Invoices": "عرض فواتير المريض",
    "View Treatment": "عرض المعالجة",
    "View and manage all your clinic appointments interactively from one dashboard": "عرض وإدارة جميع مواعيد عيادتك تفاعلياً من لوحة تحكم واحدة",
    "View appointment information without editing": "عرض معلومات الموعد بدون تعديل",
    "View treatment information without editing": "عرض معلومات المعالجة بدون تعديل",
    "Visit Date": "تاريخ الزيارة",
    "Wednesday": "الأربعاء",
    "WhatsApp": "واتساب",
    "Whitening": "تبييض الأسنان",
    "Working Days of the Week": "أيام العمل في الأسبوع",
    "Working Hours": "ساعات العمل",
    "Yes, Delete Appointment": "نعم، احذف الموعد",
    "Yes, Delete Patient": "نعم، احذف المريض",
    "Yes, Delete Treatment": "نعم، احذف المعالجة",
    "You": "أنت",
    "done sessions": "جلسات منجزة",
    "e.g., $, USD, EUR, SAR": "مثال: $, USD, EUR, SAR",
    "e.g., Cleaning": "مثال: تنظيف وتلميع",
    "from one practical dashboard": "من لوحة تحكم عملية واحدة",
    "invoiced treatments": "المعالجات المفوترة",
    "invoices automatically": "الفواتير تلقائياً",
    "payments collected": "المدفوعات المحصلة",
    "treatments, and payments in one place": "المعالجات، والمدفوعات في مكان واحد",
    "waiting sessions": "جلسات قيد الانتظار",
    "العربية": "العربية",
    "System Backups": "نسخ النظام الاحتياطية",
    "Create database backups and manage historical restore points": "إنشاء نسخ احتياطية لقاعدة البيانات وإدارة نقاط الاستعادة التاريخية",
    "Create Backup Now": "إنشاء نسخة احتياطية الآن",
    "Backup File Name": "اسم ملف النسخة الاحتياطية",
    "Creation Date": "تاريخ الإنشاء",
    "Size": "الحجم",
    "Download Backup": "تحميل النسخة الاحتياطية",
    "Delete Backup": "حذف النسخة الاحتياطية",
    "No backup files found. Click \"Create Backup Now\" to make a new database snapshot.": "لم يتم العثور على ملفات نسخ احتياطي. انقر فوق \"إنشاء نسخة احتياطية الآن\" لإنشاء لقطة جديدة لقاعدة البيانات.",
    "Are you sure you want to delete this backup file?": "هل أنت متأكد من رغبتك في حذف ملف النسخة الاحتياطية هذا؟",
    "Backup created successfully:": "تم إنشاء النسخة الاحتياطية بنجاح:",
    "Failed to create database backup:": "فشل إنشاء النسخة الاحتياطية لقاعدة البيانات:",
    "Backup file not found.": "ملف النسخة الاحتياطية غير موجود.",
    "Backup file deleted successfully.": "تم حذف ملف النسخة الاحتياطية بنجاح.",
    "Failed to delete backup file.": "فشل حذف ملف النسخة الاحتياطية.",
    "Create Backup": "إنشاء نسخة احتياطية",
    "Notifications & Reminders": "الإشعارات والتذكيرات",
    "Notifications": "الإشعارات",
    "Configure automated reminders via Email, SMS, and WhatsApp": "تهيئة التذكيرات التلقائية عبر البريد الإلكتروني ورسائل SMS والواتساب",
    "Setup & API Keys": "الإعداد ومفاتيح الواجهة البرمجية (API)",
    "Sent Notification Log": "سجل الإشعارات المرسلة",
    "Enable Channels": "تفعيل القنوات",
    "Enable SMS Reminders (Twilio)": "تفعيل التذكير عبر رسائل SMS (تويليو)",
    "Sends text messages to patient mobile numbers 24 hours and 2 hours before their appointments.": "يرسل رسائل نصية إلى أرقام هواتف المرضى المحمولة قبل 24 ساعة وساعتين من مواعيدهم.",
    "Enable WhatsApp Reminders (Twilio WhatsApp API)": "تفعيل التذكير عبر واتساب (تويليو واتساب API)",
    "Sends automated WhatsApp notifications to patient phone numbers.": "يرسل إشعارات واتساب تلقائية إلى أرقام هواتف المرضى.",
    "Enable Email Reminders (SMTP)": "تفعيل التذكير عبر البريد الإلكتروني (SMTP)",
    "Sends HTML/Text emails to patient email addresses.": "يرسل رسائل بريد إلكتروني نصية/HTML إلى عناوين البريد الإلكتروني للمرضى.",
    "Twilio SMS & WhatsApp Credentials": "بيانات اعتماد SMS وواتساب من تويليو",
    "If Twilio keys are not provided, reminders will be logged to local logs for testing purposes without sending actual messages.": "إذا لم يتم توفير مفاتيح تويليو، فسيتم تسجيل التذكيرات في السجلات المحلية لأغراض الاختبار دون إرسال رسائل فعلية.",
    "Twilio Account SID": "معرف الحساب (Account SID) من تويليو",
    "Twilio Auth Token": "رمز المصادقة (Auth Token) من تويليو",
    "Twilio From Number (SMS)": "رقم المرسل من تويليو (SMS)",
    "Twilio WhatsApp Sandbox/Number": "صندوق رمل / رقم واتساب من تويليو",
    "SMTP Email Server Credentials": "بيانات اعتماد خادم البريد الإلكتروني SMTP",
    "SMTP Host": "مضيف SMTP",
    "SMTP Port": "منفذ SMTP",
    "SMTP Username (Email)": "اسم مستخدم SMTP (البريد الإلكتروني)",
    "SMTP Password / App Password": "كلمة مرور SMTP / كلمة مرور التطبيق",
    "From Email Address": "عنوان البريد الإلكتروني للمرسل",
    "Recipient": "المستلم",
    "Channel": "القناة",
    "Type": "النوع",
    "Sent Time": "وقت الإرسال",
    "Sent": "تم الإرسال",
    "Failed": "فشل",
    "No notification logs recorded yet. Reminders are checked every 5 minutes.": "لم يتم تسجيل أي سجلات إشعارات بعد. يتم فحص التذكيرات كل 5 دقائق.",
    "Invoice Details": "تفاصيل الفاتورة",
    "Detailed invoice view with treatments, payments, and current invoice status.": "عرض تفصيلي للفاتورة مع المعالجات والمدفوعات وحالة الفاتورة الحالية.",
    "Invoice Summary": "ملخص الفاتورة",
    "Subtotal": "المجموع الفرعي",
    "Discount": "الخصم",
    "Invoice Total": "إجمالي الفاتورة",
    "Remaining Balance Due": "الرصيد المتبقي المستحق",
    "Receipt #": "رقم الإيصال #",
    "Date Paid": "تاريخ الدفع",
    "Amount Paid": "المبلغ المدفوع",
    "Installment / Payment History": "سجل الأقساط / الدفع",
    "Authorized Signature & Seal": "التوقيع والختم المعتمد",
    "Bill To:": "فاتورة إلى:",
    "Date:": "التاريخ:",
    "Treatment / Procedure": "المعالجة / الإجراء",
    "Tooth": "السن",
    "Notes": "الملاحظات",
    "Price": "السعر",
    "View Appointment": "عرض الموعد",
    "Open Session": "فتح الجلسة",
    "Print Invoice": "طباعة الفاتورة",
    "Download PDF": "تحميل PDF",
    "Total Paid": "إجمالي المدفوعات",
    "Outstanding / Credit": "مستحق / رصيد",
    "Invoice Status": "حالة الفاتورة",
    "Total Payments": "إجمالي المدفوعات",
    "N/A": "غير متوفر",
    "No date": "بلا تاريخ",
    "No phone number": "لا يوجد رقم هاتف",
    "No notes available": "لا تتوفر ملاحظات",
    "No notes": "بلا ملاحظات",
    "No invoice": "لا توجد فاتورة",
    "Allocated": "مخصص",
    "View Patient": "عرض ملف المريض",
    "Back to Invoices": "العودة إلى الفواتير",
}

# Load templates/base.html
base_path = "templates/base.html"
with open(base_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# We need to find the script containing '// ── Translation Script for Arabic Language ──'
# and replace the content of that block.
# Let's inspect the block from the base.html read.
# The script is between `<script>` and `</script>` tags, wrapping lines 324-491.
# Let's define the new replacement block.

# Format the translations dictionary to JS object string
import json
json_dict = json.dumps(translations, ensure_ascii=False, indent=12)

# Build the JS script body
js_script = f"""// ── Translation Script for Arabic Language ──
    (function() {{
        const arabicTranslations = {json_dict};

        // Sort keys by length descending to match longer phrases before shorter substrings
        const sortedTranslationKeys = Object.keys(arabicTranslations).sort((a, b) => b.length - a.length);

        function escapeRegExp(string) {{
            return string.replace(/[.*+?^${{}}()|[\\\]\\\\]/g, '\\\\$&');
        }}

        // Helper to safely replace substrings in a text node value
        function safeReplace(text, key, translation) {{
            const escapedKey = escapeRegExp(key);
            // Match the key only if it is not surrounded by alphanumeric characters
            const regex = new RegExp('(?<![a-zA-Z0-9])' + escapedKey + '(?![a-zA-Z0-9])', 'gi');
            return text.replace(regex, translation);
        }}

        function translateDOM(node) {{
            if (node.nodeType === Node.TEXT_NODE) {{
                let rawText = node.nodeValue;
                let originalText = rawText;
                
                // Translate key phrases inside text node
                for (const key of sortedTranslationKeys) {{
                    rawText = safeReplace(rawText, key, arabicTranslations[key]);
                }}
                
                // Format phone numbers to prevent visual reversal in RTL/Arabic mode
                const phoneRegex = /(\\+[\\d\\s-]{{5,18}}\\d|\\b09\\d[\\d\\s-]{{4,15}}\\d)/g;
                rawText = rawText.replace(phoneRegex, (match) => {{
                    if (match.startsWith('\\u2066') && match.endsWith('\\u2069')) {{
                        return match;
                    }}
                    return '\\u2066' + match + '\\u2069';
                }});
                
                if (rawText !== originalText) {{
                    node.nodeValue = rawText;
                }}
            }} else if (node.nodeType === Node.ELEMENT_NODE) {{
                // Skip translating the script blocks, style blocks, and values inside actual input textareas/selects
                if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE') return;
                
                // Avoid modifying the value attribute of input fields, but placeholders can be translated
                const placeholder = node.getAttribute('placeholder');
                if (placeholder) {{
                    let translatedPlaceholder = placeholder;
                    for (const key of sortedTranslationKeys) {{
                        translatedPlaceholder = safeReplace(translatedPlaceholder, key, arabicTranslations[key]);
                    }}
                    if (translatedPlaceholder !== placeholder) {{
                        node.setAttribute('placeholder', translatedPlaceholder);
                    }}
                }}
                
                const titleAttr = node.getAttribute('title');
                if (titleAttr) {{
                    let translatedTitle = titleAttr;
                    for (const key of sortedTranslationKeys) {{
                        translatedTitle = safeReplace(translatedTitle, key, arabicTranslations[key]);
                    }}
                    if (translatedTitle !== titleAttr) {{
                        node.setAttribute('title', translatedTitle);
                    }}
                }}

                const tooltipAttr = node.getAttribute('data-tooltip');
                if (tooltipAttr) {{
                    let translatedTooltip = tooltipAttr;
                    for (const key of sortedTranslationKeys) {{
                        translatedTooltip = safeReplace(translatedTooltip, key, arabicTranslations[key]);
                    }}
                    if (translatedTooltip !== tooltipAttr) {{
                        node.setAttribute('data-tooltip', translatedTooltip);
                    }}
                }}

                const bsTitle = node.getAttribute('data-bs-title');
                if (bsTitle) {{
                    let translatedBsTitle = bsTitle;
                    for (const key of sortedTranslationKeys) {{
                        translatedBsTitle = safeReplace(translatedBsTitle, key, arabicTranslations[key]);
                    }}
                    if (translatedBsTitle !== bsTitle) {{
                        node.setAttribute('data-bs-title', translatedBsTitle);
                    }}
                }}

                const origTitle = node.getAttribute('data-original-title');
                if (origTitle) {{
                    let translatedOrigTitle = origTitle;
                    for (const key of sortedTranslationKeys) {{
                        translatedOrigTitle = safeReplace(translatedOrigTitle, key, arabicTranslations[key]);
                    }}
                    if (translatedOrigTitle !== origTitle) {{
                        node.setAttribute('data-original-title', translatedOrigTitle);
                    }}
                }}
                
                for (let child of node.childNodes) {{
                    translateDOM(child);
                }}
            }}
        }}

        let observer = null;
        function startObserver() {{
            if (!observer) {{
                observer = new MutationObserver((mutations) => {{
                    observer.disconnect();
                    for (let mutation of mutations) {{
                        for (let node of mutation.addedNodes) {{
                            translateDOM(node);
                        }}
                    }}
                    observer.observe(document.body, {{ childList: true, subtree: true }});
                }});
            }}
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }}

        document.addEventListener("DOMContentLoaded", function () {{
            const currentLang = document.documentElement.getAttribute('lang') || 'en';
            if (currentLang === 'ar') {{
                translateDOM(document.body);
                const title = document.title.trim();
                if (arabicTranslations[title]) {{
                    document.title = arabicTranslations[title];
                }}
                startObserver();
            }}
        }});
    }})();"""

# Replace the script block in base.html
# Find the script block. It spans from '// ── Translation Script for Arabic Language ──'
# to the end of the script tag before the next element or end of the script block.
pattern = r"// ── Translation Script for Arabic Language ──.*?\}\)\(\);"
match = re.search(pattern, html_content, re.DOTALL)
if match:
    new_html = html_content.replace(match.group(0), js_script)
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print("SUCCESS: base.html updated with comprehensive Arabic translations and observer!")
else:
    print("ERROR: Could not find translation script placeholder pattern in base.html")
