import { XRayUpload } from '@/components/vision/XRayUpload';

export default function XRayPage() {
  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Chest X-Ray Analysis 🏥</h1>
        <p className="text-gray-600">
          Upload a chest X-ray image for AI-powered analysis using Gemini Vision
        </p>
      </div>

      <XRayUpload />
    </div>
  );
}