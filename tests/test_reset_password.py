# coding: utf-8

from __future__ import unicode_literals, absolute_import

from pytest import mark

from django.core import mail
from django.core.urlresolvers import reverse

from django_factory_boy import auth as auth_factories

from tests.common_tools import template_used


@mark.django_db
def test_reset_password(client):
    """
    Testing full reset password flow, from getting to the reset password page,
    through sending email with unique token, to using that url to change the
    password.
    """

    url = reverse("password_reset")
    assert url == "/accounts/password_reset/"
    response = client.get(url)
    assert template_used(response, 'registration/password_reset_form.html')
    # make sure that we're not using default template from django admin
    assert 'Django Administration' not in response.content
    assert 'input id="id_email"' in response.content

    # --------
    response = client.post(url, {'email': 'joedoe@example.com'})
    # successful redirect, but no email sent because user doesn't exist
    assert response.status_code == 302
    assert response.url.endswith("/accounts/password_reset/done/")
    assert len(mail.outbox) == 0

    # --------
    auth_factories.UserFactory(email='joedoe@example.com')

    response = client.post(url, {'email': 'joedoe@example.com'})
    # successful redirect, and one email sent because user exists
    assert response.status_code == 302
    assert response.url.endswith("/accounts/password_reset/done/")
    assert len(mail.outbox) == 1

    response = client.get(reverse("password_reset_done"))
    assert template_used(response, 'registration/password_reset_done.html')

    # --------
    email = mail.outbox[0]
    assert email.to == ['joedoe@example.com']
    assert email.subject == 'Password reset on example.com'
    # get a relative url from the middle of the email.
    url_from_email = email.body.splitlines()[5].split('example.com')[1]

    response = client.get(url_from_email)
    # This should be a template with two password inputs
    assert template_used(response, 'registration/password_reset_confirm.html')
    assert 'Django Administration' not in response.content
    assert 'name="new_password1"' in response.content
    assert 'name="new_password2"' in response.content

    # --------
    response = client.post(url_from_email, {
        'new_password1': 'asdf',
        'new_password2': 'asdf',
    }, follow=True)
    assert template_used(response, 'registration/password_reset_complete.html')
    assert 'Django Administration' not in response.content
