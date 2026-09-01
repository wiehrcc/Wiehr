from django.urls import path
from . import views
from . import api
from wiehr import settings


urlpatterns = [
    path("", views.index, name="index"),

    path("archive/", views.archive_page, name="archive_page_slash"),
    path("archive", views.archive_page, name="archive_page"),
    path("archive/<int:slug>", views.archive_object_page, name="archive_object_page"),
    path("archive/<int:slug>/", views.archive_object_page, name="archive_object_page_slash"),

    path("globe/", views.globe_page, name="globe_page_slash"),
    path("globe", views.globe_page, name="globe_page"),
    path("globe/<str:slug>", views.globe_object_page, name="globe_object_page"),
    path("globe/<str:slug>/", views.globe_object_page, name="globe_object_page_slash"),

    path("atlas/", views.atlas_page, name="atlas_page_slash"),
    path("atlas", views.atlas_page, name="atlas_page"),
    path("atlas/<str:internal_id>", views.atlas_object_page, name="atlas_object_page"),
    path("atlas/<str:internal_id>/", views.atlas_object_page, name="atlas_object_page_slash"),

    path("lab/", views.lab_page, name="lab_page_slash"),
    path("lab", views.lab_page, name="lab_page"),
    path("lab/<str:slug>", views.lab_object_page, name="lab_object_page"),
    path("lab/<str:slug>/", views.lab_object_page, name="lab_object_page_slash"),

    path("storage", views.storage_page, name="storage_page"),
    path("storage/", views.storage_page, name="storage_page_slash"),
    path("storage/<str:slug>", views.storage_object_page, name="storage_object_page"),
    path("storage/<str:slug>/", views.storage_object_page, name="storage_object_page_slash"),
    path("storage/<str:slug>/preview", views.storage_preview_download, name="storage_preview_download"),
    path("storage/<str:slug>/preview/", views.storage_preview_download, name="storage_preview_download_slash"),
    path("storage/<str:slug>/download", views.storage_download, name="storage_download"),
    path("storage/<str:slug>/download/", views.storage_download, name="storage_download_slash"),

    path("whoareyou", views.whoareyou_page, name="whoareyou_page"),
    path("whoareyou/", views.whoareyou_page, name="whoareyou_page_slash"),

    path("engineer", views.engineer_page, name="engineer_page"),
    path("engineer/", views.engineer_page, name="engineer_page_slash"),
    path("engineer/download", views.engineer_download, name="engineer_download"),
    path("engineer/download/", views.engineer_download, name="engineer_download_slash"),

    path("composer", views.composer_page, name="composer_page"),
    path("composer/", views.composer_page, name="composer_page_slash"),
    path("composer/download", views.composer_download, name="composer_download"),
    path("composer/download/", views.composer_download, name="composer_download_slash"),

    path("s", views.shortener_page, name="shortener_page"),
    path("s/", views.shortener_page, name="shortener_page_slash"),
    path("s/qr/<int:pk>/generate", views.generate_qr, name="generate_qr"),
    path("s/qr/<int:pk>/generate/", views.generate_qr, name="generate_qr_slash"),
    path("s/qr/<int:pk>/generate_print", views.generate_print_view, name="generate_print"),
    path("s/qr/<int:pk>/generate_print/", views.generate_print_view, name="generate_print_slash"),
    path("s/<str:short_url>", views.short_redirect, name="short_redirect"),
    path("s/<str:short_url>/", views.short_redirect, name="short_redirect_slash"),

    path("licensing", views.license_page, name="license_page"),
    path("licensing/", views.license_page, name="license_page_slash"),
    path("licensing/<str:license_key>/download", views.license_download, name="license_download"),
    path("licensing/<str:license_key>/download/", views.license_download, name="license_download_slash"),

    path("privacy", views.privacy_page, name="privacy_page"),
    path("privacy/", views.privacy_page, name="privacy_page_slash"),

    path("terms", views.terms_page, name="terms_page"),
    path("terms/", views.terms_page, name="terms_page_slash"),

    path("support", views.support_page, name="support_page"),
    path("support/", views.support_page, name="support_page_slash"),

    path("disconnect", views.disconnect, name="disconnect"),
    path("disconnect/", views.disconnect, name="disconnect_slash"),
    path("disconnect/<str:token>", views.disconnect, name="disconnect_token"),
    path("disconnect/<str:token>/", views.disconnect, name="disconnect_token_slash"),

    path("api/release/<str:wid>", api.release_by_wid, name="api_release_by_wid"),
    path("api/release/<str:wid>/", api.release_by_wid, name="api_release_by_wid_slash"),
    path("api/releases", api.releases_list, name="api_releases_list"),
    path("api/releases/", api.releases_list, name="api_releases_list_slash"),
    path("api/archive/refresh", views.archive_refresh_api, name="api_archive_refresh"),
    path("api/archive/refresh/", views.archive_refresh_api, name="api_archive_refresh_slash"),
    path("api/subscribe", views.api_subscribe, name="api_subscribe"),
    path("api/subscribe/", views.api_subscribe, name="api_subscribe_slash"),
    path("api/network/locations", views.api_network_locations, name="api_network_locations"),
    path("api/network/locations/", views.api_network_locations, name="api_network_locations_slash"),

    path("ads.txt", views.ads_txt_view, name="ads_txt"),
    path("ads.txt/", views.ads_txt_view, name="ads_txt_slash"),

    path("llms.txt", views.llms_txt_view, name="llms_txt"),
    path("llms.txt/", views.llms_txt_view, name="llms_txt_slash"),

    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("robots.txt/", views.robots_txt, name="robots_txt_slash"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
    path("sitemap.xml/", views.sitemap_xml, name="sitemap_xml_slash"),
]

if settings.ENV == 'DEV':
    urlpatterns += [
        path("site.webmanifest", views.favicon, name="favicon-manifest"),
        path("favicon-16x16.png", views.favicon, name="favicon-16"),
        path("favicon-48x48.png", views.favicon, name="favicon-48"),
        path("favicon-96x96.png", views.favicon, name="favicon-96"),
        path("favicon.svg", views.favicon, name="favicon-svg"),
        path("favicon.png", views.favicon, name="favicon-png"),
        path("favicon.ico", views.favicon, name="favicon"),
        path("apple-touch-icon.png", views.favicon, name="favicon-apple"),
        path("web-app-manifest-192x192.png", views.favicon, name="web-app-manifest-192"),
        path("web-app-manifest-512x512.png", views.favicon, name="web-app-manifest-512"),
        path("404", views.handler404, name="404-dev"),
        path("500", views.handler500, name="500-dev")
    ]
