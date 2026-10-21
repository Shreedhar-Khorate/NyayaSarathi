"""
NyayaSarathi AI Legal Translation Service
Supports Indic languages (Hindi, Marathi)
Preserves legal citation formatting (e.g., Section 438 CrPC, BNS §103)
"""
import os
import re
from typing import Optional
from schemas.translate import TranslationRequest, TranslationResponse

LANGUAGE_NAMES = {
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
    "en": "English",
}

# Translation replacements for legal narrative terms & takeaways
COMMON_LEGAL_TERMS = {
    "hi": [
        (r"Historical judicial analysis indicates notable headwinds \((.*?) estimated favorable probability\) for the applicant\.", r"ऐतिहासिक न्यायिक विश्लेषण आवेदक के लिए उल्लेखनीय प्रतिकूल परिस्थितियों (\1 अनुमानित अनुकूल संभावना) का संकेत देता है।"),
        (r"Historical judicial analysis indicates a strongly favorable precedent alignment \((.*?) estimated favorable probability\) for the applicant\.", r"ऐतिहासिक न्यायिक विश्लेषण आवेदक के लिए एक दृढ़ता से अनुकूल मिसाल संरेखण (\1 अनुमानित अनुकूल संभावना) को दर्शाता है।"),
        (r"Precedent analysis indicates a balanced judicial posture \((.*?) estimated probability\) for the applicant\. Historical rulings show outcomes are discretionary and heavily dependent on specific factual documentation, clean antecedents, and the persuasiveness of arguments presented\.", r"पूर्ववर्ती विश्लेषण आवेदक के लिए संतुलित न्यायिक स्थिति (\1 अनुमानित संभावना) का संकेत देता है। ऐतिहासिक फैसले बताते हैं कि परिणाम विवेकाधीन हैं और विशिष्ट तथ्यात्मक दस्तावेजों, निष्कलंक पूर्ववृत्त और तर्कों की प्रभावशीलता पर अत्यधिक निर्भर हैं।"),
        (r"Comparable High Court rulings reflect stricter judicial scrutiny, suggesting that key opposition arguments regarding statutory bars or evidentiary standards must be addressed proactively\.", r"तुलनात्मक उच्च न्यायालय के फैसले सख्त न्यायिक जांच को दर्शाते हैं, जिससे पता चलता है कि वैधानिक बाधाओं या साक्ष्य मानकों के संबंध में विरोध के तर्कों का सक्रिय रूप से समाधान किया जाना चाहिए।"),
        (r"Statutory alignment: Case is grounded in recognized provisions under (.*)\.", r"वैधानिक संरेखण: मामला \1 के तहत मान्यता प्राप्त प्रावधानों पर आधारित है।"),
        (r"Procedural standing: The petition/claim invokes established remedies within the High Court's jurisdiction\.", r"प्रक्रियात्मक स्थिति: याचिका उच्च न्यायालय के अधिकार क्षेत्र के भीतर स्थापित उपायों का आह्वान करती है।"),
        (r"Adverse precedent risk: In (.*?), the court ordered (.*?) due to severity of allegations or evidentiary thresholds\.", r"प्रतिकूल मिसाल का जोखिम: \1 के मामले में, अदालत ने आरोपों की गंभीरता या साक्ष्य की सीमा के कारण \2 का आदेश दिया।"),
        (r"Prosecution objections: The State/prosecution may oppose relief citing prima facie evidence, gravity of charges, or necessity of custodial investigation\.", r"अभियोजन आपत्तियां: राज्य/अभियोजन पक्ष प्रथम दृष्टया साक्ष्य, आरोपों की गंभीरता या हिरासत में पूछताछ की आवश्यकता का हवाला देकर राहत का विरोध कर सकता है।"),
        (r"Precedent grant: In (.*?), the court ruled (.*?) under comparable facts\.", r"मिसाल की मंजूरी: \1 में, अदालत ने समान तथ्यों के तहत \2 का आदेश दिया।"),
        (r"Favorable precedent density: (.*?) closely ranked historical cases secured favorable or partially allowed relief\.", r"अनुकूल मिसाल घनत्व: \1 ऐतिहासिक मामलों ने अनुकूल या आंशिक रूप से स्वीकृत राहत हासिल की।"),
        (r"\bFavorable\b", "अनुकूल"),
        (r"\bUnfavorable\b", "प्रतिकूल"),
        (r"\bBalanced / Discretionary\b", "संतुलित / विवेकपूर्ण"),
        (r"\bWITHDRAWN\b", "वापस लिया गया (WITHDRAWN)"),
        (r"\bDISPOSED\b", "निपटाया गया (DISPOSED)"),
        (r"\bALLOWED\b", "स्वीकृत (ALLOWED)"),
        (r"\bDISMISSED\b", "खारिज (DISMISSED)"),
        (r"\bBAIL GRANTED\b", "जमानत मंजूर (BAIL GRANTED)"),
        (r"\bLegal Notice\b", "कानूनी नोटिस (Legal Notice)"),
        (r"\bBail Application\b", "जमानत याचिका (Bail Application)"),
        (r"\bPetition\b", "याचिका (Petition)"),
        (r"\bWritten Statement\b", "लिखित कथन (Written Statement)"),
        (r"\bReply\b", "प्रत्युत्तर / जवाब (Reply)"),
        (r"\bStatement of Material Facts\b", "मुख्य तथ्यों का विवरण"),
        (r"\bParticulars of Breach\b", "उल्लंघन एवं चूक का विवरण"),
        (r"\bGrounds for Grant of Bail\b", "जमानत मंजूर करने के आधार"),
        (r"\bPrayer for Relief\b", "राहत के लिए प्रार्थना"),
        (r"\bVerification & Attestation\b", "सत्यापन एवं साक्ष्यांकन"),
        (r"\bPreliminary Objections\b", "प्रारंभिक आपत्तियां"),
        (r"\bPara-wise Specific Denial\b", "प्रत्येक पैरा का विशिष्ट खंडन"),
        (r"\bSynopsis & Chronological Sequence\b", "संक्षेप एवं कालानुक्रमिक विवरण"),
        (r"\bAffidavit in Support\b", "समर्थन में शपथ पत्र"),
        (r"\bPeremptory Demand\b", "अंतिम मांग एवं नोटिस अवधि"),
    ],
    "mr": [
        (r"Historical judicial analysis indicates notable headwinds \((.*?) estimated favorable probability\) for the applicant\.", r"ऐतिहासिक न्यायालयीन विश्लेषण अर्जासाठी प्रतिकूल परिस्थितीचे संकेत (\1 अंदाजित अनुकूल संभाव्यता) देते."),
        (r"Historical judicial analysis indicates a strongly favorable precedent alignment \((.*?) estimated favorable probability\) for the applicant\.", r"ऐतिहासिक न्यायालयीन विश्लेषण अर्जासाठी अनुकूल दृष्टांत जुळणी (\1 अंदाजित अनुकूल संभाव्यता) दर्शवते."),
        (r"Precedent analysis indicates a balanced judicial posture \((.*?) estimated probability\) for the applicant\. Historical rulings show outcomes are discretionary and heavily dependent on specific factual documentation, clean antecedents, and the persuasiveness of arguments presented\.", r"दृष्टांत विश्लेषण अर्जासाठी संतुलित न्यायालयीन भूमिकेचा (\1 अंदाजित संभाव्यता) निर्देश करते. ऐतिहासिक निकाल दर्शवतात की निकाल हे विवेकबुद्धीनुसार आहेत आणि विशिष्ट तथ्यात्मक दस्तऐवज, स्वच्छ पार्श्वभूमी आणि युक्तिवादाच्या प्रभावीपणावर अवलंबून असतात."),
        (r"Comparable High Court rulings reflect stricter judicial scrutiny, suggesting that key opposition arguments regarding statutory bars or evidentiary standards must be addressed proactively\.", r"तुलनात्मक उच्च न्यायालयाचे निकाल अधिक कडक न्यायालयीन छाननी दर्शवतात, ज्यामुळे कायदेशीर अडथळे किंवा पुराव्यांच्या मानकांबाबत विरोधी युक्तिवादांना प्राधान्याने सामोरे जाणे आवश्यक आहे."),
        (r"Statutory alignment: Case is grounded in recognized provisions under (.*)\.", r"वैधानिक सुसंगतता: खटला \1 अंतर्गत मान्यताप्राप्त तरतुदींवर आधारित आहे."),
        (r"Procedural standing: The petition/claim invokes established remedies within the High Court's jurisdiction\.", r"प्रक्रियेत्मक दर्जा: याचिका उच्च न्यायालयाच्या अधिकारक्षेत्रातील प्रस्थापित उपायांचा वापर करते."),
        (r"Adverse precedent risk: In (.*?), the court ordered (.*?) due to severity of allegations or evidentiary thresholds\.", r"प्रतिकूल दृष्टांत धोका: \1 प्रकरणात, न्यायालयाने आरोपांचे गांभीर्य किंवा पुराव्यांच्या मर्यादेमुळे \2 चा आदेश दिला."),
        (r"Prosecution objections: The State/prosecution may oppose relief citing prima facie evidence, gravity of charges, or necessity of custodial investigation\.", r"अभियोजन आक्षेप: राज्य/सरकारी पक्ष प्रथमदर्शनी पुरावे, आरोपांचे गांभीर्य किंवा कोठडीतील तपासाच्या आवश्यकतेचा हवाला देऊन अर्जास विरोध करू शकतो."),
        (r"Precedent grant: In (.*?), the court ruled (.*?) under comparable facts\.", r"दृष्टांत मंजुरी: \1 मध्ये, न्यायालयाने समान तथ्यांच्या आधारे \2 चा निकाल दिला."),
        (r"Favorable precedent density: (.*?) closely ranked historical cases secured favorable or partially allowed relief\.", r"अनुकूल दृष्टांत घनता: \1 ऐतिहासिक प्रकरणांनी अनुकूल किंवा अंशतः मंजूर दिलासा मिळवला."),
        (r"\bFavorable\b", "अनुकूल"),
        (r"\bUnfavorable\b", "प्रतिकूल"),
        (r"\bBalanced / Discretionary\b", "संतुलित / विवेकबुद्धीनुसार"),
        (r"\bWITHDRAWN\b", "मागे घेतले (WITHDRAWN)"),
        (r"\bDISPOSED\b", "निकाल लावला (DISPOSED)"),
        (r"\bALLOWED\b", "मंजूर (ALLOWED)"),
        (r"\bDISMISSED\b", "फेटाळले (DISMISSED)"),
        (r"\bBAIL GRANTED\b", "जामीन मंजूर (BAIL GRANTED)"),
        (r"\bLegal Notice\b", "कायदेशीर नोटीस (Legal Notice)"),
        (r"\bBail Application\b", "जामीन अर्ज (Bail Application)"),
        (r"\bPetition\b", "याचिका (Petition)"),
        (r"\bWritten Statement\b", "लेखी जबाब (Written Statement)"),
        (r"\bReply\b", "प्रत्युत्तर / उत्तर (Reply)"),
        (r"\bStatement of Material Facts\b", "महत्त्वाच्या तथ्यांचे विवरण"),
        (r"\bParticulars of Breach\b", "उल्लंघन आणि त्रुटींचे तपशील"),
        (r"\bGrounds for Grant of Bail\b", "जामीन मंजूर करण्याचे आधार"),
        (r"\bPrayer for Relief\b", "दिलासा मिळण्यासाठी विनंती"),
        (r"\bVerification & Attestation\b", "पडताळणी आणि साक्षांकन"),
        (r"\bPreliminary Objections\b", "प्राथमिक आक्षेप"),
        (r"\bPara-wise Specific Denial\b", "प्रत्येक परिच्छेदाचे विशिष्ट खंडन"),
        (r"\bSynopsis & Chronological Sequence\b", "संक्षेप आणि कालानुक्रमिक तपशील"),
        (r"\bAffidavit in Support\b", "समर्थनार्थ शपथपत्र"),
        (r"\bPeremptory Demand\b", "अंतिम मागणी आणि नोटीस मुदत"),
    ]
}


def translate_legal_text(request: TranslationRequest, is_drafting_feature: bool = False) -> TranslationResponse:
    text = request.text.strip()
    target_lang = request.target_language.lower()

    if target_lang == "en" or not text:
        return TranslationResponse(
            translated_text=text,
            source_language=request.source_language or "en",
            target_language=target_lang,
            provider="Native Engine"
        )

    # Deterministic legal replacement dictionary
    translated = text
    if target_lang in COMMON_LEGAL_TERMS:
        for pattern, repl in COMMON_LEGAL_TERMS[target_lang]:
            translated = re.sub(pattern, repl, translated)

    # Clean fallback: remove bracket prefix if text was partially replaced
    if translated == text:
        lang_name = LANGUAGE_NAMES.get(target_lang, target_lang.upper())
        translated = f"[{lang_name}] {text}"

    return TranslationResponse(
        translated_text=translated,
        source_language=request.source_language or "en",
        target_language=target_lang,
        provider="NyayaSarathi Legal NLP Engine"
    )



