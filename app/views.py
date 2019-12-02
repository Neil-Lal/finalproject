"""
Definition of views.
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponseRedirect
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.models import User
from django.db.models import Sum, Max
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from sqlalchemy import create_engine
from datetime import datetime

import pandas as pd
import os.path

from .models import Reports, ExecutiveSummaryData
from .forms import ContactForm


def home(request):
    """Renders the home page."""
    context = {
        'title':'Upload data',
    }
    if request.user.is_authenticated:
        user = get_object_or_404(User, pk=request.user.id)
        context['permission'] = user.has_perm('app.can_view')


    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
        }
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
                send_mail(subject, message, from_email, [email.email for email in superusers_emails]) #superusers_emails
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
                'title':'Contact',
                'message':'Let me know if you have any questions, comments, or concerns.',
                'form': form,
            }
        )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
        }
    )

def simple_upload(request):
    """Allows users with Uploader permissions to upload data"""
    user = get_object_or_404(User, pk=request.user.id)
    context = {
        'permission': user.has_perm('app.can_upload'),    
        'reports': Reports.objects.all(),
        'title':'Upload data',
    }

    # Arriving by POST
    if request.method == 'POST' and request.FILES['myfile']:
        # Verify again that user is allowed to upload data
        if not user.has_perm('app.can_upload'):
            messages.error(request, 'Need uploader permissions')
            return HttpResponseRedirect(reverse('upload'))
        ### ADD A TRY STATEMENT WHEN DONE

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
            df = pd.read_csv(myfile, header=0, skip_blank_lines=True, 
                    skipinitialspace=True)
        elif myfile.name.endswith('.xls') or myfile.name.endswith('.xlsx'):
            df = pd.read_excel(myfile)
        else:
            messages.error(request, 'Invalid file type uploaded')
            return HttpResponseRedirect(reverse('upload'))

        # Add date ran and foreign key values
        today = datetime.today().strftime('%Y-%m-%d')
        df['date_ran'] = today
        df['name_id'] = fk_name

        # Validate required fields
        required_fields = [requ.strip() for requ in required_fields.split(',')]
        for field in required_fields:
            if field not in df.columns:
                messages.error(request, 'Column: ' + str(field) + 
                               ' is missing from file.  Please try again.')
                return HttpResponseRedirect(reverse('upload'))

        # Upload to django database
        engine = create_engine(database_url, echo=False)
        connection = engine.raw_connection()
        df.to_sql('app_executivesummarydata', con=connection, index=False, if_exists='append')
        
        return render(request, 'app/upload.html', context)

    return render(request, 'app/upload.html', context)

    # Render list page with the documents and the form

