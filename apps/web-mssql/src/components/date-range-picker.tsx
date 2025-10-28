import { useState } from "react";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import { Calendar as CalendarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface DateRangePickerProps {
  dateFrom?: string;
  dateTo?: string;
  onDateFromChange: (date: string) => void;
  onDateToChange: (date: string) => void;
}

export function DateRangePicker({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
}: DateRangePickerProps) {
  const [openFrom, setOpenFrom] = useState(false);
  const [openTo, setOpenTo] = useState(false);

  const fromDate = dateFrom ? new Date(dateFrom) : undefined;
  const toDate = dateTo ? new Date(dateTo) : undefined;

  return (
    <div className="space-y-2">
      <Popover open={openFrom} onOpenChange={setOpenFrom}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className="w-full justify-start text-left font-normal h-8"
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {fromDate
              ? format(fromDate, "dd 'de' MMMM 'de' yyyy", { locale: es })
              : "Desde..."}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={fromDate}
            onSelect={(date) => {
              if (date) {
                onDateFromChange(date.toISOString().split("T")[0]);
              }
              setOpenFrom(false);
            }}
            disabled={(date) => toDate ? date > toDate : false}
            initialFocus
            locale={es}
          />
        </PopoverContent>
      </Popover>

      <Popover open={openTo} onOpenChange={setOpenTo}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className="w-full justify-start text-left font-normal h-8"
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {toDate
              ? format(toDate, "dd 'de' MMMM 'de' yyyy", { locale: es })
              : "Hasta..."}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={toDate}
            onSelect={(date) => {
              if (date) {
                onDateToChange(date.toISOString().split("T")[0]);
              }
              setOpenTo(false);
            }}
            disabled={(date) => fromDate ? date < fromDate : false}
            initialFocus
            locale={es}
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
