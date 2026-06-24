from django.conf import settings
from django.db import models


class Transaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='transactions',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    public_id = models.CharField(max_length=40, unique=True)
    card_id = models.CharField(max_length=20)
    merchant_name = models.CharField(max_length=120)
    category = models.CharField(max_length=40)
    amount = models.IntegerField()
    approved_at = models.DateTimeField()
    payment_type = models.CharField(max_length=20, default='lump_sum')
    installment_months = models.PositiveSmallIntegerField(default=0)
    is_interest_free_installment = models.BooleanField(default=False)
    icon = models.CharField(max_length=8, default='💳')
    address = models.CharField(max_length=200, blank=True, default='직접 입력')
    source_text = models.TextField(blank=True, default='')
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-approved_at', '-id']
        indexes = [
            models.Index(fields=['user', '-approved_at']),
            models.Index(fields=['card_id', '-approved_at']),
            models.Index(fields=['category', '-approved_at']),
        ]

    def __str__(self):
        return f'{self.merchant_name} {self.amount}'


class OwnedCard(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='owned_cards',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    card_id = models.CharField(max_length=20)
    nickname = models.CharField(max_length=80, blank=True, default='')
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['user', 'card_id'], name='api_owned_user_card_uniq'),
        ]
        indexes = [
            models.Index(fields=['user', 'display_order', 'id']),
            models.Index(fields=['display_order', 'id']),
        ]

    def __str__(self):
        return self.nickname or self.card_id


class AuthSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='carch_sessions', on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)
    provider = models.CharField(max_length=20, default='email')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'{self.user_id} {self.provider}'


class SocialAccount(models.Model):
    PROVIDERS = [
        ('kakao', '카카오'),
        ('naver', '네이버'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='social_accounts', on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    provider_user_id = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default='')
    name = models.CharField(max_length=80, blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')
    raw_profile = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'provider_user_id'],
                name='api_social_provider_user_uniq',
            ),
        ]
        indexes = [
            models.Index(fields=['provider', 'provider_user_id']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'{self.provider}:{self.provider_user_id}'


class PurchasePlan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='purchase_plans',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=120)
    plan_type = models.CharField(max_length=40, default='기타')
    expense_mode = models.CharField(max_length=40, default='planned-extra')
    total_budget = models.PositiveIntegerField(default=0)
    start_month = models.CharField(max_length=7)
    end_month = models.CharField(max_length=7)
    status = models.CharField(max_length=30, default='작성 중')
    selected_scenario_id = models.CharField(max_length=40, blank=True, default='')
    progress = models.PositiveSmallIntegerField(default=0)
    items = models.JSONField(default=list, blank=True)
    scenarios = models.JSONField(default=list, blank=True)
    analysis_record = models.ForeignKey(
        'AIAnalysisRecord',
        related_name='purchase_plans',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title


class CommunityPost(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='community_posts',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=120)
    body = models.TextField()
    author = models.CharField(max_length=30, default='남주현')
    avatar = models.CharField(max_length=2, default='남')
    tags = models.JSONField(default=list, blank=True)
    likes = models.PositiveIntegerField(default=0)
    liked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return self.title


class CommunityComment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='community_comments',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(CommunityPost, related_name='comment_set', on_delete=models.CASCADE)
    body = models.TextField()
    author = models.CharField(max_length=30, default='남주현')
    avatar = models.CharField(max_length=2, default='남')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f'{self.author}: {self.body[:20]}'


class CommunityPostLike(models.Model):
    post = models.ForeignKey(CommunityPost, related_name='like_set', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='community_likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_community_post_like'),
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['post', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user_id}:{self.post_id}'


class AIAnalysisRecord(models.Model):
    ANALYSIS_TYPES = [
        ('spending_summary', '소비 분석'),
        ('chat', '챗봇 상담'),
        ('transaction_parse', '결제내역 입력 보정'),
        ('purchase_plan', '소비 계획 분석'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='ai_analysis_records',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    analysis_type = models.CharField(max_length=40, choices=ANALYSIS_TYPES)
    cache_key = models.CharField(max_length=80, blank=True, default='')
    title = models.CharField(max_length=120, blank=True)
    input_payload = models.JSONField(default=dict, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    ai_mode = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'analysis_type', '-created_at']),
            models.Index(fields=['analysis_type', '-created_at']),
            models.Index(
                fields=['analysis_type', 'cache_key', '-created_at'],
                name='api_ai_cache_idx',
            ),
        ]

    def __str__(self):
        return f'{self.analysis_type}: {self.title or self.created_at}'
