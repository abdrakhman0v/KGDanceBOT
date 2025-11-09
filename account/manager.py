from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, telegram_id, username, role, phone, first_name, last_name, parent=None):
        user = self.model(telegram_id=telegram_id,
                          username=username,
                          role=role,
                          phone=phone,
                          first_name=first_name,
                          last_name=last_name,
                          parent=parent)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', 'admin')
        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user 
        
