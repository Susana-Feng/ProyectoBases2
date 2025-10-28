import ExcelUploader from "@/components/excel-uploader";

export default function IndexPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-background to-muted/20">
      <ExcelUploader />
    </div>
  );
}
