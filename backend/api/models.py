from django.db import models


class Transaction(models.Model):
    public_id = models.CharField(max_length=40, unique=True)
    card_id = models.CharField(max_length=20)
    merchant_name = models.CharField(max_length=120)
    category = models.CharField(max_length=40)
    amount = models.IntegerField()
    approved_at = models.DateTimeField()
    icon = models.CharField(max_length=8, default='💳')
    address = models.CharField(max_length=200, blank=True, default='직접 입력')
    source_text = models.TextField(blank=True, default='')
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-approved_at', '-id']
        indexes = [
            models.Index(fields=['card_id', '-approved_at']),
            models.Index(fields=['category', '-approved_at']),
        ]

    def __str__(self):
        return f'{self.merchant_name} {self.amount}'


class OwnedCard(models.Model):
    card_id = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=80, blank=True, default='')
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'id']
        indexes = [
            models.Index(fields=['display_order', 'id']),
        ]

    def __str__(self):
        return self.nickname or self.card_id


class PurchasePlan(models.Model):
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
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title


class CommunityPost(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField()
    author = models.CharField(max_length=30, default='김지훈')
    avatar = models.CharField(max_length=2, default='김')
    tags = models.JSONField(default=list, blank=True)
    likes = models.PositiveIntegerField(default=0)
    liked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CommunityComment(models.Model):
    post = models.ForeignKey(CommunityPost, related_name='comment_set', on_delete=models.CASCADE)
    body = models.TextField()
    author = models.CharField(max_length=30, default='김지훈')
    avatar = models.CharField(max_length=2, default='김')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author}: {self.body[:20]}'


class AIAnalysisRecord(models.Model):
    ANALYSIS_TYPES = [
        ('spending_summary', '소비 분석'),
        ('chat', '챗봇 상담'),
        ('transaction_parse', '결제내역 입력 보정'),
        ('purchase_plan', '소비 계획 분석'),
    ]

    analysis_type = models.CharField(max_length=40, choices=ANALYSIS_TYPES)
    title = models.CharField(max_length=120, blank=True)
    input_payload = models.JSONField(default=dict, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    ai_mode = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis_type', '-created_at']),
        ]

    def __str__(self):
        return f'{self.analysis_type}: {self.title or self.created_at}'
