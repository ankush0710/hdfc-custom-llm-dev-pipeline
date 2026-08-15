const TextAreaField = ({
  label,
  name,
  placeholder = "",
  value,
  onChange,
  rows = 4,
}) => {
  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={name}
        className="text-[14px] font-medium uppercase tracking-wide text-[#002B5C]"
      >
        {label}
      </label>

      <textarea
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={rows}
        className="w-full resize-none rounded-sm border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none placeholder:text-slate-400 focus:border-[#004C97] focus:ring-1 focus:ring-[#004C97]"
      />
    </div>
  );
};

export default TextAreaField;
