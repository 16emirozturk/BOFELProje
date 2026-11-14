"""Güvenli Okul v3.0: rapor, yedek, takvim ve içerik yardımcıları."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

import db


def pdf_proje_raporu(dil: str = "Türkçe") -> bytes:
    """Kişisel bildirim açıklamalarını içermeyen toplu proje raporu üretir."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    font_candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path(__file__).with_name("DejaVuSans.ttf"),
    ]
    font_path = next((p for p in font_candidates if p.exists()), None)
    if font_path:
        pdfmetrics.registerFont(TTFont("GOSans", str(font_path)))
        font = "GOSans"
    else:
        font = "Helvetica"

    lang = dil
    texts = {
        "Türkçe": ["Güvenli Okul — Proje Özeti", "Bu rapor demo verileri ve toplu istatistiklerle oluşturulmuştur.", "Toplam bildirim", "Açık bildirim", "Önleyici çalışma", "Önemli not", "Kural tabanlı öncelik sinyalleri karar değildir. Bildirim sayısındaki değişim, zorbalığın gerçek sıklığını veya bir çalışmanın nedensel etkisini kanıtlamaz."],
        "English": ["Güvenli Okul — Project Summary", "Generated from demonstration data and aggregate statistics.", "Total reports", "Open reports", "Preventive activities", "Important note", "Rule-based priority signals are not decisions. Changes in report counts do not prove the true frequency of bullying or causal impact."],
        "Deutsch": ["Güvenli Okul — Projektübersicht", "Erstellt aus Demodaten und aggregierten Statistiken.", "Meldungen gesamt", "Offene Meldungen", "Präventionsmaßnahmen", "Wichtiger Hinweis", "Regelbasierte Prioritätssignale sind keine Entscheidungen. Änderungen der Meldezahlen belegen weder die tatsächliche Häufigkeit noch eine kausale Wirkung."],
        "Français": ["Güvenli Okul — Synthèse du projet", "Établi à partir de données de démonstration et de statistiques agrégées.", "Signalements au total", "Signalements ouverts", "Actions de prévention", "Remarque importante", "Les signaux de priorité fondés sur des règles ne sont pas des décisions. L’évolution du nombre de signalements ne prouve ni la fréquence réelle ni un effet causal."],
        "Español": ["Güvenli Okul — Resumen del proyecto", "Generado a partir de datos de demostración y estadísticas agregadas.", "Informes totales", "Informes abiertos", "Actividades preventivas", "Nota importante", "Las señales de prioridad basadas en reglas no son decisiones. Los cambios en el número de informes no demuestran la frecuencia real ni un efecto causal."],
        "العربية": ["Güvenli Okul — ملخص المشروع", "أُنشئ باستخدام بيانات تجريبية وإحصاءات مجمعة.", "إجمالي البلاغات", "البلاغات المفتوحة", "أنشطة الوقاية", "ملاحظة مهمة", "إشارات الأولوية القائمة على القواعد ليست قرارات. ولا تثبت التغيرات في عدد البلاغات معدل التنمر الفعلي أو وجود أثر سببي."],
        "Azərbaycan dili": ["Güvenli Okul — Layihə xülasəsi", "Demo məlumatları və ümumiləşdirilmiş statistika əsasında yaradılıb.", "Ümumi bildiriş", "Açıq bildiriş", "Profilaktik fəaliyyət", "Vacib qeyd", "Qayda əsaslı prioritet siqnalları qərar deyil. Bildiriş sayındakı dəyişiklik zorakılığın real tezliyini və ya səbəb-nəticə təsirini sübut etmir."],
    }
    t = texts.get(lang, texts["Türkçe"])
    if lang == "العربية":
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            t = [get_display(arabic_reshaper.reshape(x)) for x in t]
        except ImportError:
            # The required packages are listed in requirements.txt; this fallback
            # keeps PDF generation available if a local install is incomplete.
            pass
    records = db.kayitlari_getir(limit=100000)
    open_count = sum(1 for r in records if r.get("durum") != "Sonuçlandırıldı")
    activities = db.onleyici_ozeti().get("Toplam", 0)
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("GOTitle", parent=styles["Title"], fontName=font, alignment=TA_CENTER, textColor=colors.HexColor("#17345B"), fontSize=18, leading=24)
    body = ParagraphStyle("GOBody", parent=styles["BodyText"], fontName=font, fontSize=9, leading=14)
    heading = ParagraphStyle("GOHeading", parent=styles["Heading2"], fontName=font, textColor=colors.HexColor("#17345B"), fontSize=12)
    story = [Paragraph(t[0], title), Spacer(1, 8*mm), Paragraph(t[1], body), Spacer(1, 5*mm)]
    data = [[t[2], str(len(records))], [t[3], str(open_count)], [t[4], str(activities)]]
    table = Table(data, colWidths=[110*mm, 35*mm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#F1F5FA")), ("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#172B4D")), ("FONTNAME",(0,0),(-1,-1),font), ("FONTSIZE",(0,0),(-1,-1),10), ("GRID",(0,0),(-1,-1),.4,colors.HexColor("#D8E1EC")), ("PADDING",(0,0),(-1,-1),8)]))
    story += [table, Spacer(1, 8*mm), Paragraph(t[5], heading), Paragraph(t[6], body), Spacer(1, 8*mm), Paragraph(datetime.now(db.TZ).strftime("%d.%m.%Y %H:%M"), body)]
    doc.build(story)
    return out.getvalue()


def takvim_uyarilari() -> list[dict]:
    """Yaklaşan ve gecikmiş önleyici çalışmalar; yalnızca yönetim ekranında gösterilir."""
    today = datetime.now(db.TZ).date()
    alerts = []
    for item in db.onleyici_calismalari_getir():
        if item["durum"] in ("Tamamlandı", "İptal edildi"):
            continue
        try:
            due = datetime.strptime(item["planlanan_tarih"], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        days = (due - today).days
        if days < 0:
            alerts.append({"type": "overdue", "days": abs(days), "item": item})
        elif days <= 14:
            alerts.append({"type": "upcoming", "days": days, "item": item})
    return sorted(alerts, key=lambda a: (a["type"] != "overdue", a["days"]))


EGITIM_KARTLARI = [
    {"title": "Akran zorbalığını tanımak", "summary": "Tekrarlayan, güç dengesizliği içeren davranışları; tek seferlik anlaşmazlıklardan ayırt etmeye yardımcı bilgiler.", "steps": ["Davranışın tekrar edip etmediğine bakın.", "Taraflar arasındaki güç dengesizliğini değerlendirin.", "Etiket koymadan, somut davranışı ve etkisini anlatın."]},
    {"title": "Dijital güvenlik", "summary": "Çevrim içi ortamda saygı, mahremiyet ve güvenli destek arama yolları.", "steps": ["Kişisel bilgileri ve başkalarının özel içeriklerini paylaşmayın.", "Rahatsız edici iletişime yanıt vermek zorunda değilsiniz.", "Güvendiğiniz bir yetişkinden destek isteyin."]},
    {"title": "Tanık olanlar ne yapabilir?", "summary": "Güvenli ve destekleyici müdahale yolları.", "steps": ["Güvenli değilse doğrudan müdahale etmeyin.", "Dışlamaya katılmayın; destekleyici bir tutum gösterin.", "Durumu güvenilir bir yetişkine bildirin."]},
    {"title": "Destek istemek", "summary": "Yardım istemek güçsüzlük değildir; güvenilir yetişkinler ve okul destek birimleriyle konuşun.", "steps": ["Kendinizi güvende hissettiğiniz yetişkini seçin.", "Ne olduğunu ve nasıl etkilendiğinizi anlatın.", "Acil tehlikede yerel acil yardım hizmetlerine başvurun."]},
]

HELP_STEPS = [
    ("1. Bildirim gönder", "Yeni bildirim sayfasında olay türü, ortam ve zaman bilgilerini seçin. Gerçek ad, telefon veya başka kişisel bilgi yazmayın."),
    ("2. Takip kodunu sakla", "Gönderimden sonra oluşan kodu güvenli bir yerde saklayın. Kod, bildirimin durumunu sorgulamak içindir."),
    ("3. Durumu takip et", "Bildirim sorgula alanında takip kodunu girin. Öğrenci ekranında açıklama ve inceleme notları gösterilmez."),
    ("4. Yetkili incelemesi", "Yetkili personel bildirimi insan değerlendirmesiyle inceler. Otomatik sinyaller tek başına karar vermez."),
]
