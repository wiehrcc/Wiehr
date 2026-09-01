from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import *
from wiehr import settings


def invert_hex_color(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return '#ffffff'
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    inverted = tuple(255 - c for c in rgb)
    return '#{:02x}{:02x}{:02x}'.format(*inverted)


class TeamCampaignActionForm(ActionForm):
    campaign_title = forms.CharField(
        label='Email title',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Email Title (appears in browser tab)', 'size': 40})
    )
    campaign_subject = forms.CharField(
        label='Email subject',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Subject', 'size': 40})
    )
    campaign_body = forms.CharField(
        label='Message',
        required=True,
        widget=forms.Textarea(attrs={'placeholder': 'Main text (HTML)', 'rows': 12,
                                     'style': 'font-family:monospace;width:100%'})
    )
    campaign_button_text = forms.CharField(
        label='Button label',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Listen'})
    )
    campaign_button_url = forms.URLField(
        label='Button URL',
        required=False,
        widget=forms.URLInput(attrs={'placeholder': 'https://wiehr.cc'})
    )


class TeamCampaignForm(forms.Form):
    internal_id = forms.CharField(
        label='Release ID',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Enter release ID for custom colors'})
    )
    subject = forms.CharField(
        label='Email Subject',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Enter email subject'})
    )
    title = forms.CharField(
        label='Email Title',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Email Title (appears in browser tab)'})
    )
    body = forms.CharField(
        label='Email Body',
        required=True,
        widget=forms.Textarea(attrs={'rows': 14, 'style': 'font-family:monospace;width:100%'})
    )
    button_text = forms.CharField(
        label='Button Text',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'Optional button text'})
    )
    button_url = forms.URLField(
        label='Button URL',
        required=False,
        widget=forms.URLInput(attrs={'class': 'vURLField', 'placeholder': 'https://example.com'})
    )
    tags = forms.CharField(
        label='Tags',
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'class': 'vTextField', 'placeholder': 'e.g., #synthetic #electronic #drumnbass'})
    )
    test_email = forms.EmailField(
        label='Test Email',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'vTextField', 'placeholder': 'your@email'})
    )


class LabArchiveActionForm(ActionForm):
    archive_target = forms.ModelChoiceField(
        label='Archive year',
        queryset=WiehrArchiveModel.objects.order_by('-year'),
        required=False,
        empty_label='— pick a year —',
    )


admin.site.site_header = "Wiehr"
admin.site.site_title = "𝄃𝄃𝄂𝄂𝄀𝄁𝄃𝄂𝄂𝄃"
admin.site.index_title = "🌐"


@admin.register(WiehrGlobeObjectArtist)
class WiehrGlobeObjectArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', )
    readonly_fields = ('created_at', )
    list_per_page = 25
    
    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('name', )
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class WiehrLabObjectLinkInline(admin.TabularInline):
    model = WiehrLabObjectLink
    extra = 1
    fields = ('website', 'url', 'description', 'order')


@admin.register(WiehrLabModel)
class WiehrLabModelAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'title', 'project_type', 'r_media', 'order', 'role', 'release_type', 'start_year', 'end_year', 'slug', 'is_visible', 'created_at')
    list_filter = ('release_type', 'is_visible', 'start_year', 'end_year', 'created_at')
    search_fields = ('internal_id', 'title', 'project_type', 'description', 'role', 'slug')
    readonly_fields = ('created_at', 'modified_at', 'r_media_large')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [WiehrLabObjectLinkInline]
    list_per_page = 25
    list_editable = ('order', 'is_visible')
    filter_horizontal = ('extra_archives',)
    action_form = LabArchiveActionForm
    actions = ['add_to_archive', 'remove_from_archive']

    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('internal_id', 'title', 'project_type', 'slug', 'role', 'release_type')
        }),
        ('📅 Years', {
            'fields': ('start_year', 'end_year', 'extra_archives'),
            'description': (
                'End year 0 renders as "Present". An item shows automatically under its '
                'start year only — use "Also show in these years" to surface ongoing work '
                'in later archives too.'
            )
        }),
        ('🖼️ Media', {
            'fields': ('media', 'r_media_large', 'youtube_url'),
            'description': 'One file per item. GIF is stored untouched so it keeps animating. If YouTube URL is set, clicking the cover opens it in a modal.'
        }),
        ('📄 Content', {
            'fields': ('description', 'order', 'is_visible')
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

    @mark_safe
    def r_media(self, obj):
        if obj.media:
            return f'<img src="{obj.media.url}" height="40px"/>'
        return '❌'
    r_media.short_description = 'Media'

    @mark_safe
    def r_media_large(self, obj):
        if obj.media:
            return f'<img src="{obj.media.url}" style="max-width: 320px; max-height: 320px;"/>'
        return 'No media'
    r_media_large.short_description = 'Preview'

    def _archive_from_request(self, request):
        archive_id = request.POST.get('archive_target')
        if not archive_id:
            return None
        return WiehrArchiveModel.objects.filter(pk=archive_id).first()

    @admin.action(description='➕ Add selected to archive year')
    def add_to_archive(self, request, queryset):
        archive = self._archive_from_request(request)
        if not archive:
            self.message_user(
                request, 'Pick an archive year in the dropdown first.', messages.WARNING
            )
            return
        for item in queryset:
            item.extra_archives.add(archive)
        archive.refresh_counts()
        self.message_user(
            request,
            f'Added {queryset.count()} Lab item(s) to {archive.year}. '
            f'{archive.year} now lists {archive.lab_count} Lab item(s).',
        )

    @admin.action(description='➖ Remove selected from archive year')
    def remove_from_archive(self, request, queryset):
        archive = self._archive_from_request(request)
        if not archive:
            self.message_user(
                request, 'Pick an archive year in the dropdown first.', messages.WARNING
            )
            return
        for item in queryset:
            item.extra_archives.remove(archive)
        archive.refresh_counts()
        self.message_user(
            request,
            f'Removed {queryset.count()} Lab item(s) from {archive.year}. '
            f'{archive.year} now lists {archive.lab_count} Lab item(s).',
        )


@admin.register(WiehrLabObjectLink)
class WiehrLabObjectLinkAdmin(admin.ModelAdmin):
    list_display = ('lab', 'website', 'r_url', 'description', 'order')
    list_filter = ('lab', 'website')
    search_fields = ('website', 'description', 'url')
    list_per_page = 50

    @mark_safe
    def r_url(self, obj):
        if obj.url:
            return f'<a target="_blank" href="{obj.url}">🔗 Open Link</a>'
        return '-'
    r_url.short_description = 'Link'


class WiehrGlobeObjectToWiehrArtistObjectInline(admin.TabularInline):
    model = WiehrGlobeObjectToWiehrArtistObject
    extra = 1
    fields = ('artist_object', 'role', 'order')
    autocomplete_fields = ['artist_object']


class WiehrGlobeObjectCreditsInline(admin.TabularInline):
    model = WiehrGlobeObjectCredits
    extra = 1
    fields = ('artist_object', 'credit_type', 'notes', 'order')
    autocomplete_fields = ['artist_object']


@admin.register(WiehrGlobeModel)
class WiehrGlobeModelAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'title', 'get_artists', 'date', 'release_type', 'year', 'order', 'r_image', 'r_color_preview', 'tags_preview', 'is_visible', 'is_out')
    list_filter = ('is_visible', 'is_out', 'release_type', 'year', 'date')
    search_fields = ('internal_id', 'title', 'tags', 'slug')
    readonly_fields = ('created_at', 'r_image_large', 'r_color_preview_large')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [WiehrGlobeObjectToWiehrArtistObjectInline, WiehrGlobeObjectCreditsInline]
    date_hierarchy = 'date'
    list_per_page = 25
    list_editable = ('order', 'is_visible', 'is_out')
    
    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('internal_id', 'title', 'date', 'slug', 'release_type', 'year', 'order', 'is_visible', 'is_out')
        }),
        ('📄 Content', {
            'fields': ('pitch', 'tags')
        }),
        ('🌍 Geographic', {
            'fields': ('geo',),
            'description': 'Enter coordinates in format: 054° 03\' 28.7" N 008° 22\' 44.3" W'
        }),
        ('🎨 Design', {
            'fields': ('background_color', 'r_color_preview_large', 'image', 'r_image_large')
        }),
        ('🔗 Links', {
            'fields': ('listen_url', 'lyrics_url', 'watch_url', 'pdf_file')
        }),
        ('⚙️ System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_hidden', 'mark_as_shown']
    
    def get_artists(self, obj):
        artists = [ra.artist_object.name for ra in obj.artist_roles.all()[:3]]
        return ", ".join(artists) if artists else "-"
    get_artists.short_description = 'Artists'

    @admin.action(description='🚫 Hide selected releases')
    def mark_as_hidden(self, request, queryset):
        count = queryset.update(is_visible=False)
        self.message_user(request, f'{count} release(s) marked as hidden.')

    @admin.action(description='✅ Show selected releases')
    def mark_as_shown(self, request, queryset):
        count = queryset.update(is_visible=True)
        self.message_user(request, f'{count} release(s) marked as visible.')

    @mark_safe
    def r_image(self, obj):
        if obj.image:
            return f'<img src="/{settings.MEDIA_URL}{obj.image}" height="50px"/>'
        return '❌'
    r_image.short_description = 'Cover'
    
    @mark_safe
    def r_image_large(self, obj):
        if obj.image:
            return f'<img src="/{settings.MEDIA_URL}{obj.image}" style="max-width: 400px; max-height: 400px;"/>'
        return 'No Image'
    r_image_large.short_description = 'Cover Preview'
    
    @mark_safe
    def r_color_preview(self, obj):
        if obj.background_color:
            return format_html(
                '<div style="background-color: {}; width: 50px; height: 20px; border: 1px solid #ccc; border-radius: 0;" title="{}"></div>',
                obj.background_color, obj.background_color
            )
        return '-'
    r_color_preview.short_description = 'Color'
    
    @mark_safe
    def r_color_preview_large(self, obj):
        if obj.background_color:
            return format_html(
                '<div style="background-color: {}; width: 200px; height: 50px; border: 2px solid #ccc; border-radius: 0; display: flex; align-items: center; justify-content: center; font-family: monospace; font-weight: bold;">{}</div>',
                obj.background_color, obj.background_color
            )
        return '-'
    r_color_preview_large.short_description = 'Background Color Preview'
    
    def tags_preview(self, obj):
        if obj.tags:
            tags = obj.tags[:50] + '...' if len(obj.tags) > 50 else obj.tags
            return tags
        return '-'
    tags_preview.short_description = 'Tags'


@admin.register(WiehrGlobeObjectToWiehrArtistObject)
class WiehrGlobeObjectToWiehrArtistObjectAdmin(admin.ModelAdmin):
    list_display = ('artist_object', 'globe_object', 'role', 'order')
    list_filter = ('role', 'artist_object__name', 'globe_object__title')
    search_fields = ('artist_object__name', 'globe_object__title')
    list_per_page = 50
    list_editable = ('role', 'order')
    autocomplete_fields = ['artist_object', 'globe_object']


@admin.register(WiehrGlobeObjectCredits)
class WiehrGlobeObjectCreditsAdmin(admin.ModelAdmin):
    list_display = ('artist_object', 'globe_object', 'credit_type', 'notes', 'order')
    list_filter = ('credit_type',)
    search_fields = ('artist__name', 'globe_object__title', 'notes')
    list_per_page = 50
    autocomplete_fields = ['artist_object', 'globe_object']


class CVExperienceInline(admin.StackedInline):
    model = CVExperience
    extra = 0
    fields = ('role', 'company', 'company_url', 'date', 'location', 'bullets', 'order')
    ordering = ('order',)


class CVSkillInline(admin.TabularInline):
    model = CVSkill
    extra = 0
    fields = ('category', 'items', 'order')
    ordering = ('order',)


class CVProjectInline(admin.StackedInline):
    model = CVProject
    extra = 0
    fields = ('section', 'name', 'project_type', 'date', 'description', 'bullets', 'link_text', 'link_url', 'order')
    ordering = ('section', 'order')


class CVEducationInline(admin.TabularInline):
    model = CVEducation
    extra = 0
    fields = ('title', 'date', 'url', 'order')
    ordering = ('order',)


class CVLanguageInline(admin.TabularInline):
    model = CVLanguage
    extra = 0
    fields = ('language', 'level', 'order')
    ordering = ('order',)


@admin.register(CVProfile)
class CVProfileAdmin(admin.ModelAdmin):
    list_display = ('version', 'name', 'title', 'updated_at')
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Profile', {
            'fields': ('version', 'name', 'title', 'bio')
        }),
        ('Contact', {
            'fields': ('email', 'location', 'linkedin', 'linkedin_url', 'website')
        }),
    )
    inlines = [CVExperienceInline, CVSkillInline, CVProjectInline, CVEducationInline, CVLanguageInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from .cv_builder import invalidate_cv_cache
        invalidate_cv_cache(obj.version)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        from .cv_builder import invalidate_cv_cache
        invalidate_cv_cache(form.instance.version)


class WiehrAtlasObjectImageInline(admin.TabularInline):
    model = WiehrAtlasObjectImage
    extra = 1
    fields = ('image', 'order')
    ordering = ('order',)


@admin.register(WiehrAtlasModel)
class WiehrAtlasModelAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'country_code', 'country_title', 'release_type', 'year', 'order', 'is_visible', 'created_at')
    list_filter = ('release_type', 'is_visible', 'year', 'country_code', 'created_at')
    search_fields = ('internal_id', 'country_code', 'country_title', 'coordinates')
    readonly_fields = ('created_at', 'modified_at')
    list_editable = ('is_visible', 'order')
    list_per_page = 25
    inlines = [WiehrAtlasObjectImageInline]
    
    fieldsets = (
        ('📍 Location Info', {
            'fields': ('internal_id', 'country_code', 'country_title', 'release_type', 'year', 'order')
        }),
        ('🌍 Coordinates', {
            'fields': ('coordinates',),
            'description': 'Enter coordinates in format: 41° 41\' 49.5672" N 44° 46\' 25.2264" E'
        }),
        ('⚙️ Settings', {
            'fields': ('is_visible',)
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )
    

@admin.register(WiehrAtlasObjectImage)
class WiehrAtlasObjectImageAdmin(admin.ModelAdmin):
    list_display = ('atlas_object', 'r_image_preview', 'order', 'created_at', )
    list_filter = ('atlas_object', 'created_at', )
    search_fields = ('atlas__country_title', )
    readonly_fields = ('created_at', 'r_image_large', )
    list_editable = ('order',)
    list_per_page = 50
    
    fieldsets = (
        ('📍 Location', {
            'fields': ('atlas_object',)
        }),
        ('🖼️ Image', {
            'fields': ('image', 'r_image_large')
        }),
        ('⚙️ Settings', {
            'fields': ('order',)
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    @mark_safe
    def r_image_preview(self, obj):
        if obj.image:
            return f'<img src="/{settings.MEDIA_URL}{obj.image}" height="50px"/>'
        return '❌'
    r_image_preview.short_description = 'Preview'
    
    @mark_safe
    def r_image_large(self, obj):
        if obj.image:
            return f'<img src="/{settings.MEDIA_URL}{obj.image}" style="max-width: 400px; max-height: 400px;"/>'
        return 'No Image'
    r_image_large.short_description = 'Image Preview'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('email', 'country', 'country_code', 'is_blacklist', 'is_disconnected', 'disconnected_at', 'created_at', 'updated_at')
    list_filter = ('is_blacklist', 'is_disconnected', 'country', 'created_at')
    search_fields = ('email', 'country')
    list_editable = ('is_blacklist', 'is_disconnected')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'disconnected_at')
    change_list_template = 'admin/web/team/change_list.html'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('campaign/', self.admin_site.admin_view(self.campaign_view), name='team_campaign'),
            path('campaign/preview/', self.admin_site.admin_view(self.campaign_preview), name='team_campaign_preview'),
        ]
        return custom_urls + urls

    def campaign_view(self, request):
        from django.shortcuts import render
        from django.http import JsonResponse
        from .email_utils import send_team_campaign
        from .models import Team

        if request.method == 'POST':
            form = TeamCampaignForm(request.POST)
            if form.is_valid():
                title = form.cleaned_data.get('title')
                subject = form.cleaned_data['subject']
                body = form.cleaned_data['body']
                button_text = form.cleaned_data.get('button_text')
                button_url = form.cleaned_data.get('button_url')
                test_email = form.cleaned_data.get('test_email')
                wid = form.cleaned_data.get('wid')
                tags = form.cleaned_data.get('tags')

                bg_color = '#f4f4f4'
                text_color = '#151617'
                action = request.POST.get('action')

                if action == 'test':
                    if not test_email:
                        messages.error(request, 'Please provide a test email address.')
                    else:
                        from .email_utils import send_templated_email
                        context = {
                            'title': title,
                            'headline': title or subject,
                            'body': body,
                            'button_text': button_text,
                            'button_url': button_url,
                            'bg_color': bg_color,
                            'text_color': text_color,
                            'tags': tags,
                        }
                        sent = send_templated_email(subject, [test_email], "emails/team_campaign.html", context)
                        messages.success(request, f'Test campaign sent to {test_email}.')
                else:
                    queryset = Team.objects.filter(is_blacklist=False, is_disconnected=False)

                    try:
                        sent = send_team_campaign(
                            subject=subject,
                            body=body,
                            title=title,
                            button_text=button_text,
                            button_url=button_url,
                            queryset=queryset,
                            extra_context={'bg_color': bg_color, 'text_color': text_color, 'tags': tags}
                        )
                        messages.success(request, f'Campaign sent successfully to {sent} subscribers.')
                        form = TeamCampaignForm()
                    except Exception as exc:
                        messages.error(request, f'Failed to send campaign: {exc}')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = TeamCampaignForm()

        total_subscribers = Team.objects.filter(is_blacklist=False, is_disconnected=False).count()

        context = {
            'form': form,
            'total_subscribers': total_subscribers,
            'title': 'Team Campaign Management',
        }
        return render(request, 'admin/web/team/campaign.html', context)

    def campaign_preview(self, request):
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        if request.method == 'POST':
            form = TeamCampaignForm(request.POST)
            if form.is_valid():
                title = form.cleaned_data.get('title')
                subject = form.cleaned_data['subject']
                body = form.cleaned_data['body']
                button_text = form.cleaned_data.get('button_text')
                button_url = form.cleaned_data.get('button_url')
                wid = form.cleaned_data.get('wid')
                tags = form.cleaned_data.get('tags')

                bg_color = '#f4f4f4'
                text_color = '#151617'

                context = {
                    'title': title,
                    'headline': title or subject,
                    'body': body,
                    'button_text': button_text,
                    'button_url': button_url,
                    'site_url': getattr(settings, 'SITE_URL', ''),
                    'bg_color': bg_color,
                    'text_color': text_color,
                    'tags': tags,
                }
                html_content = render_to_string('emails/team_campaign.html', context)

                return HttpResponse(html_content)
            else:
                return HttpResponse('Invalid form data', status=400)
        else:
            return HttpResponse('Method not allowed', status=405)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['campaign_url'] = 'campaign/'
        return super().changelist_view(request, extra_context)


@admin.register(WiehrArchiveModel)
class WiehrArchiveModelAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'year', 'total_count', 'globe_count', 'atlas_count', 'lab_count', 'storage_count', 'is_visible', 'modified_at')
    list_filter = ('is_visible', 'year')
    search_fields = ('internal_id',)
    readonly_fields = ('created_at', 'modified_at', 'globe_count', 'atlas_count', 'lab_count', 'storage_count', 'total_count')
    list_editable = ('is_visible',)
    list_per_page = 25
    ordering = ('-year',)
    
    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('internal_id', 'year', 'is_visible')
        }),
        ('📊 Counts (Auto-calculated)', {
            'fields': ('total_count', 'globe_count', 'atlas_count', 'lab_count', 'storage_count'),
            'classes': ('collapse',)
        }),
        ('📋 Cached IDs', {
            'fields': ('globe_ids', 'atlas_ids', 'lab_ids', 'storage_ids'),
            'classes': ('collapse',)
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['refresh_counts']
    
    @admin.action(description='🔄 Refresh counts for selected archives')
    def refresh_counts(self, request, queryset):
        for archive in queryset:
            archive.refresh_counts()
        self.message_user(request, f'Refreshed counts for {queryset.count()} archive(s).')


class WiehrStorageLinkInline(admin.TabularInline):
    model = WiehrStorageLinkModel
    extra = 1
    fields = ('label', 'url', 'order')


class LicenseInline(admin.TabularInline):
    model = License
    extra = 0
    fields = ('internal_id', 'license_key', 'license_type', 'licensee_name', 'is_active')
    readonly_fields = ('internal_id', 'license_key')
    show_change_link = True


@admin.register(WiehrStorageModel)
class WiehrStorageModelAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'title', 'file_type', 'price_display', 'year', 'order', 'access_type', 'download_count', 'is_visible', 'created_at')
    list_filter = ('is_visible', 'access_type', 'currency', 'file_type', 'year')
    search_fields = ('internal_id', 'title', 'description', 'slug')
    readonly_fields = ('created_at', 'modified_at', 'file_size', 'download_count')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('order', 'is_visible')
    list_per_page = 25
    inlines = [WiehrStorageLinkInline, LicenseInline]

    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('internal_id', 'title', 'slug', 'file_type', 'year', 'order')
        }),
        ('📄 Content', {
            'fields': ('description', 'cover_image')
        }),
        ('📁 File', {
            'fields': ('file', 'file_size', 'download_count')
        }),
        ('💵 Price', {
            'fields': ('price', 'currency', 'purchase_url'),
            'description': 'Leave Price empty and the item is free — nothing renders. '
                           'With a Price set, /storage marks the cell and the item page shows the amount. '
                           'A price on its own does not gate the file: to actually sell it, set Access Type to '
                           '"License Key Required" and put the shop link in Purchase URL, so the locked download '
                           'offers BUY, and the key you issue on purchase unlocks it.'
        }),
        ('👁️ Preview', {
            'fields': ('preview_type', 'preview_url'),
            'description': "audio/image previews are your own uploaded files; video previews use a YouTube URL, same as Lab"
        }),
        ('🔒 Access Control', {
            'fields': ('is_visible', 'access_type', 'access_password', 'auto_issue_license_type'),
            'description': 'public = visible to all, link = anyone with URL, password = requires password, license_key = requires a valid License (see Licenses below), auto_issue = visitor enters Legal Name + Email and a License of the type below is created for them automatically, auto_issue_password = same but password-gated first. Auto-issue License Type is required when using either auto_issue option.'
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Shortener)
class ShortenerAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'r_long_url', 'full_url', 'times_followed', 'created_at')
    search_fields = ('short_url', 'full_url', 'long_url')
    list_filter = ('created_at',)
    # short_url is editable so links can be named from the admin too;
    # blank still falls back to a generated code on save.
    readonly_fields = ('full_url', 'times_followed', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 50

    fieldsets = (
        ('🔗 Link', {
            'fields': ('long_url', 'short_url', 'full_url'),
            'description': 'Short code is generated on save. Links can also be created at /s without opening admin.'
        }),
        ('📊 Stats', {
            'fields': ('times_followed', 'created_at')
        }),
    )

    def r_long_url(self, obj):
        return obj.long_url[:60] + ('…' if len(obj.long_url) > 60 else '')
    r_long_url.short_description = 'Long URL'


@admin.register(ShortenerSettings)
class ShortenerSettingsAdmin(admin.ModelAdmin):
    list_display = ('password', 'modified_at')
    fields = ('password',)

    def has_add_permission(self, request):
        return not ShortenerSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        ShortenerSettings.load()
        return super().changelist_view(request, extra_context)


@admin.action(description='🖨 Generate Print PDF')
def generate_print_action(modeladmin, request, queryset):
    for qr_code in queryset:
        try:
            pdf_path = qr_code.generate_print()
            messages.success(request, f'Print PDF generated for {qr_code}: {pdf_path}')
        except Exception as exc:
            messages.error(request, f'Error generating print for {qr_code}: {exc}')


@admin.register(QrCode)
class QrCodeAdmin(admin.ModelAdmin):
    list_display = ('object_id', 'wid', 'tag', 'link', 'r_generate_qr', 'r_generate_print', 'created_at')
    search_fields = ('object_id', 'wid', 'tag', 'link')
    list_filter = ('tag', 'created_at')
    ordering = ('-created_at',)
    actions = [generate_print_action]
    list_per_page = 25

    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('object_id', 'tag', 'link', 'wid'),
            'description': 'Setting a WID pulls the colours from that release.'
        }),
        ('🎨 QR Configuration', {
            'fields': ('error_correction', 'version', 'border', 'fg_color', 'bg_color', 'logo_size', 'svg_size')
        }),
    )

    @mark_safe
    def r_generate_qr(self, obj):
        return f'<a class="button" href="/s/qr/{obj.pk}/generate" target="_blank">Generate QR</a>'
    r_generate_qr.short_description = 'QR Code'

    @mark_safe
    def r_generate_print(self, obj):
        return f'<a class="button" href="/s/qr/{obj.pk}/generate_print" target="_blank">Generate Print</a>'
    r_generate_print.short_description = 'Print PDF'


@admin.register(LicenseType)
class LicenseTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.action(description='📄 Download agreements (ZIP: PDF + DOCX + TXT)')
def download_agreements_action(modeladmin, request, queryset):
    import io
    import zipfile
    from django.http import HttpResponse
    from .license_builder import build_agreement_docx, build_agreement_pdf, build_agreement_text

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for licence in queryset.select_related('license_type', 'product_storage'):
            base = f'WIEHR_LICENSE_{licence.internal_id}'
            archive.writestr(f'{base}.txt', build_agreement_text(licence).encode('utf-8'))
            archive.writestr(f'{base}.pdf', build_agreement_pdf(licence))
            archive.writestr(f'{base}.docx', build_agreement_docx(licence))

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    count = queryset.count()
    name = 'wiehr_licenses.zip' if count > 1 else f'WIEHR_LICENSE_{queryset.first().internal_id}.zip'
    response['Content-Disposition'] = f'attachment; filename="{name}"'
    return response


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('internal_id', 'licensee_name', 'license_type', 'r_product', 'is_active', 'effective_date', 'r_documents')
    list_filter = ('license_type', 'is_active', 'effective_date')
    search_fields = ('internal_id', 'license_key', 'licensee_name', 'licensee_email', 'product_text')
    readonly_fields = ('internal_id', 'license_key', 'created_at', 'modified_at', 'r_documents_large')
    autocomplete_fields = ['product_storage']
    list_per_page = 25
    actions = [download_agreements_action]

    fieldsets = (
        ('🪪 Identity', {
            'fields': ('internal_id', 'license_key', 'is_active'),
            'description': 'Both are auto-generated on first save if left blank.'
        }),
        ('👤 Licensee', {
            'fields': ('licensee_name', 'licensee_email')
        }),
        ('📦 Product', {
            'fields': ('product_storage', 'product_text'),
            'description': 'Link a real Storage item, or describe the product as free text if it has none.'
        }),
        ('📜 Terms', {
            'fields': ('license_type', 'effective_date')
        }),
        ('📄 Signed agreement', {
            'fields': ('r_documents_large',),
            'description': 'Generated live from the fields above — nothing is stored on disk.'
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )

    def r_product(self, obj):
        return obj.get_product_display()
    r_product.short_description = 'Product'

    @mark_safe
    def r_documents(self, obj):
        if not obj.license_key:
            return '—'
        base = f'/licensing/{obj.license_key}/download'
        return (
            f'<a href="{base}?fmt=pdf" target="_blank">PDF</a> · '
            f'<a href="{base}?fmt=docx" target="_blank">DOCX</a> · '
            f'<a href="{base}?fmt=txt" target="_blank">TXT</a>'
        )
    r_documents.short_description = 'Agreement'

    @mark_safe
    def r_documents_large(self, obj):
        if not obj.pk or not obj.license_key:
            return 'Save the license first — the key is generated on save.'
        base = f'/licensing/{obj.license_key}/download'
        buttons = ''.join(
            f'<a class="button" href="{base}?fmt={fmt}" target="_blank" '
            f'style="margin-right:8px;">Download {fmt.upper()}</a>'
            for fmt in ('pdf', 'docx', 'txt')
        )
        verify = f'/licensing?key={obj.license_key}'
        return (
            f'{buttons}<p style="margin-top:10px;">'
            f'Public verification: <a href="{verify}" target="_blank">{verify}</a></p>'
        )
    r_documents_large.short_description = 'Download'
