"""
Definition of views.
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.contrib.auth.models import User, Group
from django.db.models import Sum, Max
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from sqlalchemy import create_engine
from datetime import datetime
from io import BytesIO

import pandas as pd
import os.path

from .models import Reports, ExecutiveSummaryData, accountingJE_GLMapping, Announcements, ExportReports, Schedule
from .forms import ContactForm


def home(request):
    """Renders the home page."""
    context = {
        'title': 'Upload data',
        # Admin can enter announcements in admin panel - Shows TODAYS announcements
        'announcements': Announcements.objects.filter(date=datetime.today())
    }
    send_reports()  ##REMOVEEEEE
    # View for logged in users
    if request.user.is_authenticated:
        user = get_object_or_404(User, pk=request.user.id)

        # Get last upload dates for reports that expands and contracts with table
        upload_dates = {}
        report_list = Reports.objects.all().values('name').annotate(max_date=Max('report_name__date_ran'))
        for report in report_list:
            # Get latest date
            date = report['max_date'].strftime('%m/%d/%Y')

            # Check if date is in current month for formatting
            if report['max_date'].strftime('%m') == datetime.today().strftime('%m'):
                date_class = 'current'
            else:
                date_class = 'not_current'
            vals = {'date': date, 'date_class': date_class}
            upload_dates[report['name']] = vals

        # Add to context - upload dates and permission settings
        context['upload_dates'] = upload_dates
        context['permissions'] = user.has_perm('app.can_view')
        context['accounting'] = user.has_perm('accounting_view')

    # Render page with context
    return render(
        request,
        'app/index.html',
        context
    )


def process_accounting_JE(type='Debits and Credits Journal Entry'):
    """Get Executive summary data and process into Journal Entry(JE) report format"""

    # Default value for type incase weird value somehow gets passed to type
    qs = ExportReports.objects.all().values('name')
    types = [qs[i]['name'] for i in range(len(qs))]
    type = type if type in types else 'Debits and Credits Journal Entry'

    def add_gl(row):
        """Helper function for  mapping GL #s to locations"""
        gl = accountingJE_GLMapping.objects.all()
        loc = row['location']
        gl_value = gl.filter(location=loc).values('GL')[0]['GL']
        return gl_value

    # Get data for latest monthly Journal Entry (JE) report
    data_accounting_JE_latest_date = ExecutiveSummaryData.objects \
                                                         .latest('date_ran') \
                                                         .date_ran

    # Create a pandas dataframe for data processing
    data_accounting_JE = ExecutiveSummaryData.pdobjects \
                                             .filter(date_ran=data_accounting_JE_latest_date) \
                                             .to_dataframe()

    # Remove unecessary columns
    if type == 'Debits and Credits Journal Entry':
        data_accounting_JE = data_accounting_JE.drop(['id', 'date_ran', 'provider', 'name', 'charges'], axis=1)

        # Group and sums
        data_accounting_JE = data_accounting_JE.groupby(['location'], as_index=False) \
                                               .agg({'payments': 'sum', 'adjustments': 'sum'})
    if type == 'Charges Journal Entry':
        data_accounting_JE = data_accounting_JE.drop(['id', 'date_ran', 'provider', 'name', 'payments', 'adjustments'], axis=1)

        # Group and sums
        data_accounting_JE = data_accounting_JE.groupby(['location'], as_index=False) \
                                               .agg({'charges': 'sum'})
    
    # Add columns
    # GL Mapping from database
    data_accounting_JE['gl_account'] = data_accounting_JE.apply(lambda row: add_gl(row), axis=1)

    # Add Journal number with max ID
    data_accounting_JE['journal_no'] = 'JE' + str(ExecutiveSummaryData.objects.all().order_by("-id")[0].id)

    # Change location to comment with location name
    data_accounting_JE['posting_comment'] = data_accounting_JE.apply(lambda row: 'REVENUE - ' + str(row['location']), axis=1)
    data_accounting_JE = data_accounting_JE.drop(['location'], axis=1)

    # Static columns
    data_accounting_JE['post_date'] = datetime.today().strftime('%Y-%m-%d')
    data_accounting_JE['source_journal'] = 'JE'
    data_accounting_JE['source_module'] = 'GL'

    if type == 'Debits and Credits Journal Entry':
        # Reorder columns into correct upload order
        data_accounting_JE = data_accounting_JE[['gl_account', 'post_date', 'source_journal',
                                                 'journal_no', 'source_module', 'payments',
                                                 'adjustments', 'posting_comment']]

        # Rename Columns
        data_accounting_JE.columns = ['GL Account', 'Posting Date', 'Source Journal',
                                                 'Journal Number', 'Source Module', 'Debits',
                                                 'Credits', 'Posting Comment']
    if type == 'Charges Journal Entry':
        # Reorder columns into correct upload order
        data_accounting_JE = data_accounting_JE[['gl_account', 'post_date', 'source_journal',
                                                 'journal_no', 'source_module', 'charges',
                                                 'posting_comment']]

        # Rename Columns
        data_accounting_JE.columns = ['GL Account', 'Posting Date', 'Source Journal',
                                                 'Journal Number', 'Source Module',
                                                 'Charges', 'Posting Comment']

    return data_accounting_JE


def accounting(request):
    """Renders the accounting department page."""
    context = {
        'title': 'Accounting Monthly Reports',
    }

    # View for logged in users
    if request.user.is_authenticated:
        user = get_object_or_404(User, pk=request.user.id)

        # Verify correct permissions for accounting
        if user.has_perm('accounting_view'):
            context['accounting'] = user.has_perm('accounting_view')

            # Process data into reports
            data_debitsandcredits = process_accounting_JE()
            data_charges = process_accounting_JE('charges')

            # Attach to Context
            context['accoutning_JE_debitsandcredits'] = data_debitsandcredits.to_html(index=False)
            context['accoutning_JE_charges'] = data_charges.to_html(index=False)
        else:
            # No accounting permissions.  Return error message.
            messages.error(request, 'Do not have accounting permissions')
            return HttpResponseRedirect(reverse(''))
    return render(
        request,
        'app/accounting.html',
        context
    )


def download_accounting_JE(request, type='debits'):
    """Download link for accouting journal entry XLSX file"""

    data = process_accounting_JE(type)
    with BytesIO() as b:
        # Use the StringIO object as the filehandle.
        writer = pd.ExcelWriter(b, engine='xlsxwriter')
        data.to_excel(writer, sheet_name='Upload', index=False)
        writer.save()
        return HttpResponse(b.getvalue(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )


def contact(request):
    """Renders the contact page.  Allows users to send emails to specified user in settings"""

    # Arriving by POST
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Sent email to superusers group

            # Retrieve form data
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            from_email = form.cleaned_data['from_email']

            # Get superusers group and add from email address to message
            superusers_emails = User.objects.filter(is_superuser=True)
            message += '\n\n' + str(from_email)

            # Attempt to send the message via email to all superusers
            try:
                send_mail(subject,
                          message,
                          from_email,
                          [email.email for email in superusers_emails]
                          )
            except BadHeaderError:
                messages.error(request, 'Issue sending email')
                return HttpResponseRedirect(reverse('contact'))

            # Return sucesss
            messages.success(request, 'Email sent sucessfully, we will respond shortly.')
            return HttpResponseRedirect(reverse('contact'))

    # Arriving by GET
    else:

        # If user is logged in, default their account email address
        if request.user.is_authenticated:
            user = get_object_or_404(User, pk=request.user.id)
            form = ContactForm(initial={'from_email': user.email})

        # Otherwise they can enter an email address
        else:
            form = ContactForm()
        return render(
            request,
            'app/contact.html',
            {
                'title': 'Contact',
                'message': 'Let me know if you have any questions, comments, or concerns.',
                'form': form,
            }
        )


def simple_upload(request):
    """Allows users with Uploader permissions to upload data"""
    user = get_object_or_404(User, pk=request.user.id)
    context = {
        # Check if the user has uploader permissions
        'permission': user.has_perm('app.can_upload'),
        'reports': Reports.objects.all(),
        'title': 'Upload data',
    }

    # Arriving by POST
    if request.method == 'POST' and request.FILES['myfile']:

        # Server side verification that user is allowed to upload data
        if not user.has_perm('app.can_upload'):
            messages.error(request, 'Need uploader permissions')
            return HttpResponseRedirect(reverse('upload'))

        try:
            # Get uploaded file and report name and required fields
            myfile = request.FILES['myfile']
            report_name = request.POST['report_name']
            fk_name = Reports.objects.get(name=report_name).id
            required_fields = Reports.objects.get(name=report_name).required_field

            # Retrieve database settings
            database_name = settings.DATABASES['default']['NAME']
            database_url = 'sqlite:///{}'.format(os.path.abspath(database_name))

            # Convert file to dataframe for bulk upload to database
            if myfile.name.endswith('.csv'):
                df = pd.read_csv(myfile,
                                 header=0,
                                 skip_blank_lines=True,
                                 skipinitialspace=True
                                 )
            elif myfile.name.endswith('.xls') or myfile.name.endswith('.xlsx'):
                df = pd.read_excel(myfile)
            else:
                messages.error(request, 'Invalid file type uploaded')
                return HttpResponseRedirect(reverse('upload'))

            # Add date ran and foreign key values
            today = datetime.today().strftime('%Y-%m-%d')
            df['date_ran'] = today
            df['name_id'] = fk_name

            # Validate required fields using database Reports table
            required_fields = [requ.strip()
                               for requ in required_fields.split(',')]
            for field in required_fields:
                if field not in df.columns:
                    messages.error(request, 'Column: ' + str(field) +
                                   ' is missing from file.  Please try again.')
                    return HttpResponseRedirect(reverse('upload'))

            # Upload to django database
            engine = create_engine(database_url, echo=False)
            connection = engine.raw_connection()
            df.to_sql('app_executivesummarydata',
                      con=connection,
                      index=False,
                      if_exists='append'
                      )

        # Issue encountered uploading
        except Exception as e:
            messages.error(request, 'Issue uploading file to server: ' + str(e))
            return HttpResponseRedirect(reverse('upload'))
        
        # Upload complete - Send report to scheduled users
        send_reports()

    return render(request, 'app/upload.html', context)


def send_reports():
    """After upload is complete, look at Schedule table and send designated reports to designated groups"""

    # Get all reports to send out automatically
    sched = Schedule.objects.all()
    perm_group_pk = sched.values('permission_group')

    # Iter over each scheduled report
    for i in range(len(perm_group_pk)):

        # Retrieve all users in permission group to send report to
        pks = perm_group_pk[i]['permission_group']
        perm_group = Group.objects.filter(pk=pks).values('name')
        users = User.objects.filter(groups__name=perm_group[0]['name'])

        # Build email fields
        subject = sched[0].name
        message = 'See Attached'
        from_email = 'noreply@gmail.com'
        to_list = [users.values('email')[email]['email'] for email in range(len(users.values('email')))]

        # Build report
        export_pk = sched.values('report_id')[i]['report_id']
        export_name = ExportReports.objects.get(pk=export_pk).name
        report = process_accounting_JE(export_name)

        # Write report to excel
        with BytesIO() as b:
            # Use the StringIO object as the filehandle.
            writer = pd.ExcelWriter(b, engine='xlsxwriter')
            report.to_excel(writer, sheet_name='Upload', index=False)
            writer.save()

            # Attempt to email report
            try:
                email = EmailMessage(
                    subject = subject,
                    body = message,
                    from_email = from_email,
                    to = to_list,
                )
                email.attach(subject + '.xlsx',
                             b.getvalue(),
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                             )
            except BadHeaderError:
                messages.error(request, 'Issue sending email')
                return HttpResponseRedirect(reverse('contact'))
    # b.getvalue()


    """ EMAIL STUFF
            # Attempt to send the message via email to all superusers
            try:
                send_mail(subject,
                          message,
                          from_email,
                          [email.email for email in superusers_emails]
                          )
            except BadHeaderError:
                messages.error(request, 'Issue sending email')
                return HttpResponseRedirect(reverse('contact'))

            # Return sucesss
            messages.success(request, 'Email sent sucessfully, we will respond shortly.')
            return HttpResponseRedirect(reverse('contact'))
    """


def add_to_schedule(request):
    """Logic for adding Group to the schedule, if permissable"""
    pass


def schedule(request):
    """Allows user to schedule email delivery of reports"""
    context = {
        'title': 'Schedule monthly report run',
    }

    # Get today's day
    today = datetime.today().strftime('%d')

    # Serverside verification that user is logged in
    if request.user.is_authenticated:
        user = get_object_or_404(User, pk=request.user.id)

        # Verify correct permissions for accounting
        if user.has_perm('accounting_view'):
            context['accounting'] = user.has_perm('accounting_view')

            # View users scheduled reports

            # Handle deleting schedule report

            # Email report to user on UPLOAD of data

        else:
            # No accounting permissions - can't schedule their reports
            messages.error(request, 'No Accounting permissions - Cannot schedule their reports')
            return HttpResponseRedirect(reverse(''))
    else:
        # Not logged in
        messages.error(request, 'Not logged in')
        return HttpResponseRedirect(reverse('login'))
    return render(
        request,
        'app/schedule.html',
        context
    )