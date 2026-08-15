//=======================================================================================//
/*
The dataset page that shows the all information aout the datasets
*/
//=======================================================================================//
//=======================================================================================//
/*
The dataset upload page that alows us to upload any dataset (only in .csv and. jsonl format) for finetuning and training the model
*/
//=======================================================================================//
"use client";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import Footer from "@/components/layout/Footer";
import Button from "@/components/ui/Button";
import FormField from "@/components/form/FormField";
import SelectField from "@/components/form/SelectField";
import TextAreaField from "@/components/form/TextAreaField";
import FileUpload from "@/components/form/FileUpload";
import { useState } from "react";
import { Upload } from "lucide-react";

// category data which can easily change later if required

const categoryOptions = [
  {
    value: "fine-tuning",
    label: "Fine-tuning",
  },
  {
    value: "evaluation",
    label: "Evaluation",
  },
  {
    value: "validation",
    label: "Validation",
  },
];

export default function UploadDataset() {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    datasetName: "",
    category: "fine-tuning",
    version: "",
    source: "",
    description: "",
    file: null,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileSelect = (file) => {
    setFormData((prev) => ({
      ...prev,
      file,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    console.log("Dataset:", formData);
  };

  const handleCancel = () => {
    setFormData({
      datasetName: "",
      category: "fine-tuning",
      description: "",
      file: null,
    });
  };
  // Later:
  // const formDataToSend = new FormData();
  // formDataToSend.append("datasetName", formData.datasetName);
  // formDataToSend.append("category", formData.category);
  // formDataToSend.append("category", formData.version);
  // formDataToSend.append("category", formData.source);
  // formDataToSend.append("description", formData.description);
  // formDataToSend.append("file", formData.file);
  //
  // axios.post("/api/datasets", formDataToSend);

  return (
    <>
      <div className="min-h-screen bg-gray-50">
        {/* side bar consists -> all routes section */}
        <Sidebar isOpen={isOpen} onClose={() => setIsOpen(false)} />

        {/* navbar consists -> profile image and search bar section  */}
        <Navbar onMenuClick={() => setIsOpen((prev) => !prev)} />

        {/* main content of the page -> form to upload dataset  */}
        <main className="flex flex-col mt-10 pt-10 lg:pt-15 px-2 lg:px-8 lg:ml-[280px]">
          <div className="mb-6">
            <h1 className="text-[26px] font-bold text-[#002B5C]">
              Upload Dataset
            </h1>

            <p className="mt-1 text-xs text-slate-600">
              Configure and ingest new training or evaluation data into the
              platform.
            </p>
          </div>

          {/* Form Card */}
          <form
            onSubmit={handleSubmit}
            className="overflow-hidden rounded-md border border-slate-300 bg-white shadow-sm"
          >
            {/* Card Header */}
            <div className="border-b border-slate-300 px-4 py-3">
              <h2 className="text-sm font-semibold text-[#002B5C]">
                Dataset Configuration
              </h2>
            </div>

            {/* Form Content */}
            <div className="space-y-5 p-4">
              {/* Name + Category */}
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <FormField
                  label="Dataset Name"
                  name="datasetName"
                  placeholder="e.g., Financial Dataset"
                  value={formData.datasetName}
                  onChange={handleChange}
                  required
                />

                <SelectField
                  label="Category"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  options={categoryOptions}
                  required
                />

                <FormField
                  label="Dataset Version"
                  name="version"
                  placeholder="e.g. 1.0.0"
                  value={formData.version}
                  onChange={handleChange}
                  required
                />

                <FormField
                  label="Dataset Source"
                  name="source"
                  placeholder="e.g. Internal CRM"
                  value={formData.version}
                  onChange={handleChange}
                  required
                />
              </div>

              {/* Description */}
              <TextAreaField
                label="Description (Optional)"
                name="description"
                placeholder="Provide context regarding data source and intended use case..."
                value={formData.description}
                onChange={handleChange}
                rows={4}
              />

              {/* File */}
              <FileUpload onFileSelect={handleFileSelect} />
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 border-t border-slate-200 bg-[#FAFBFE] px-4 py-3">
              <Button onClick={handleCancel}>Cancel</Button>

              <Button icon={Upload} variant="primary">
                Upload
              </Button>
            </div>
          </form>
        </main>

        {/* Footer here  */}
        <div className="mt-12 lg:ml-[280px]">
          <Footer />
        </div>
      </div>
    </>
  );
}
