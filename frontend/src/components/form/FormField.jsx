const FormField = ({
  label,
  name,
  type = "text",
  placeholder = "",
  value,
  onChange,
  required = false,
}) => {
  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={name}
        className="text-[14px] font-medium uppercase tracking-wide text-[#002B5C]"
      >
        {label}
        {required && <span className="ml-1 text-red-500">*</span>}
      </label>

      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        className="h-9 w-full rounded-sm border border-slate-300 bg-white px-3 text-sm text-slate-700 outline-none transition focus:border-[#004C97] focus:ring-1 focus:ring-[#004C97]"
      />
    </div>
  );
};

export default FormField;
