const SelectField = ({
  label,
  name,
  value,
  onChange,
  options = [],
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

      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        className="h-9 w-full cursor-pointer rounded-sm border border-slate-300 bg-white px-3 text-sm text-slate-700 outline-none focus:border-[#004C97] focus:ring-1 focus:ring-[#004C97]"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default SelectField;
