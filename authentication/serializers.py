from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Utilisateur
from core.models import Membre

class UtilisateurSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'utilisateur avec toutes ses informations
    """
    nom_complet = serializers.ReadOnlyField()
    is_membre = serializers.ReadOnlyField()
    is_administrateur = serializers.ReadOnlyField()
    photo_profil_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'telephone',
            'role', 'photo_profil', 'photo_profil_url', 'nom_complet', 
            'is_membre', 'is_administrateur', 'date_creation', 'date_modification',
            'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }
    
    def get_photo_profil_url(self, obj):
        if obj.photo_profil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo_profil.url)
            return obj.photo_profil.url
        return None

class UtilisateurCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'utilisateur
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'email', 'first_name', 'last_name', 'telephone',
            'role', 'photo_profil', 'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = Utilisateur.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect")
        return value