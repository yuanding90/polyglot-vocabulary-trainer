# Azure TTS Setup Guide

## Environment Variables

Add these to your `.env.local` file:

```bash
# Azure Speech API Configuration
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus
```

## Azure Speech API Setup

1. **Get Azure Speech API Key:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create or use existing Speech Service resource
   - Copy the subscription key from "Keys and Endpoint" section
   - Note the region (e.g., eastus, westus2)

2. **Add to Environment:**
   - Create `.env.local` file in project root
   - Add your Azure Speech API key and region

3. **Features:**
   - ✅ Secure backend proxy (API key never exposed to frontend)
   - ✅ Automatic language detection from deck settings
   - ✅ High-quality Azure Neural voices
   - ✅ Browser TTS fallback
   - ✅ Audio caching for performance

## Supported Languages

- French (fr-FR-DeniseNeural)
- English (en-US-JennyNeural)
- Chinese (zh-CN-XiaoxiaoNeural)
- Spanish (es-ES-ElviraNeural)
- German (de-DE-KatjaNeural)
- Italian (it-IT-ElsaNeural)
- Japanese (ja-JP-NanamiNeural)
- Korean (ko-KR-SunHiNeural)
- Portuguese (pt-BR-FranciscaNeural)
- Russian (ru-RU-SvetlanaNeural)

## Usage

The TTS service automatically detects the language from your deck settings and uses the appropriate voice. No manual configuration needed!
