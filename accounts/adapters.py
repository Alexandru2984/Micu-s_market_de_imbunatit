# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
import re


class CustomAccountAdapter(DefaultAccountAdapter):
    def generate_unique_username(self, txts, regex=None):

        # first part of email
        if txts:
            email_part = txts[0].split('@')[0]
            # get rid of special characters
            username = re.sub(r'[^a-zA-Z0-9._-]', '', email_part)
            username = username[:30]  # limit --> 30ch
            
            # check if allready exists
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                if len(username) > 30:
                    username = f"{original_username[:25]}{counter}"
            
            return username
        
        # Fallback 
        return super().generate_unique_username(txts, regex)
    
    def populate_username(self, request, user):
        if hasattr(user, 'email') and user.email:
            username = self.generate_unique_username([user.email])
            user.username = username
