import {useRef, useState} from "react";
import {Popover, PopoverContent, PopoverTrigger} from "@/components/ui/popover";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {Label} from "@/components/ui/label";
import {ScrollArea} from "@/components/ui/scroll-area";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {X} from "lucide-react";

export interface Category {
    id: string;
    name: string;
    color: string;
}

export interface EventCategory {
    id: string;
    name: string;
    color: string;
}

export interface Event {
    id: string;
    title: string;
    categoryId?: string;
}

export interface DayData {
    date: string; // Format: YYYY-MM-DD
    categoryId?: string;
    events: Event[];
}

interface ShiftGroupDayCategoryRule {
    categoryId: string;
    eventCategoryId: string;
    eventTitles: string[];
}

export interface InteractiveCalendarProps {
    month: number; // 1-12 (January = 1)
    year: number;
    categories: Category[];
    eventCategories?: EventCategory[]; // Categories for events (for example, a preferred shift)
    initialDayData?: DayData[];
    onDayDataChange?: (dayData: DayData[]) => void;
    maxVisibleEvents?: number; // Maximum number of visible events per day (default: show all)
    showLegend?: boolean; // Whether to show the category legend (default: true)
    showCategoryTitle?: boolean; // Whether to show the category name inside the day cell (default: true)
    className?: string; // Additional CSS classes for the container element
    readOnly?: boolean; // Enables read-only mode (default: false)
    container?: HTMLElement | null; // Portal container for fullscreen mode
    view?: 'month' | 'week'; // View mode
    /** If provided, event titles are restricted to these values and shown as toggle buttons */
    allowedEventTitles?: string[];
    availabilityShiftRule?: ShiftGroupDayCategoryRule;
    wishShiftRules?: ShiftGroupDayCategoryRule[];
}

export function InteractiveCalendar({
                                        month,
                                        year,
                                        categories,
                                        eventCategories = [],
                                        initialDayData = [],
                                        onDayDataChange,
                                        maxVisibleEvents,
                                        showLegend = true,
                                        showCategoryTitle = false,
                                        className = "",
                                        readOnly = false,
                                        container,
                                        view = 'month',
                                        allowedEventTitles,
                                        availabilityShiftRule,
                                        wishShiftRules,
                                    }: InteractiveCalendarProps) {
    const [dayData, setDayData] = useState<DayData[]>(initialDayData);
    const [openPopover, setOpenPopover] = useState<string | null>(null);
    const [newEventTitle, setNewEventTitle] = useState<{ [key: string]: string }>({});
    const [selectedEventCategory, setSelectedEventCategory] = useState<{ [key: string]: string | null }>({});
    const [popoverMode, setPopoverMode] = useState<{ [key: string]: "overview" | "add-event" }>({});
    const eventIdCounter = useRef(0);

    // Default canonical order for shifts
    const DEFAULT_SHIFT_ORDER = ['F', 'S', 'N'];
    const shiftOrder = allowedEventTitles && allowedEventTitles.length > 0 ? allowedEventTitles : DEFAULT_SHIFT_ORDER;

    const sortShiftTitles = (titles: string[]) => {
        return [...titles].sort((a, b) => {
            const ia = shiftOrder.indexOf(a);
            const ib = shiftOrder.indexOf(b);
            if (ia === -1 && ib === -1) return a.localeCompare(b);
            if (ia === -1) return 1;
            if (ib === -1) return -1;
            return ia - ib;
        });
    };

    const sortEventsByShiftOrder = (events: Event[]) => {
        return [...events].sort((e1, e2) => {
            const i1 = shiftOrder.indexOf(e1.title);
            const i2 = shiftOrder.indexOf(e2.title);
            if (i1 === -1 && i2 === -1) return e1.title.localeCompare(e2.title);
            if (i1 === -1) return 1;
            if (i2 === -1) return -1;
            return i1 - i2;
        });
    };

    // Date helpers.
    const getDaysInMonth = (month: number, year: number) => {
        return new Date(year, month, 0).getDate();
    };

    const getFirstDayOfMonth = (month: number, year: number) => {
        const day = new Date(year, month - 1, 1).getDay();
        return day === 0 ? 6 : day - 1; // Monday = 0, Sunday = 6
    };

    const formatDate = (day: number) => {
        const monthStr = String(month).padStart(2, "0");
        const dayStr = String(day).padStart(2, "0");
        return `${year}-${monthStr}-${dayStr}`;
    };

    const getDayData = (date: string): DayData => {
        return dayData.find((d) => d.date === date) || {date, events: []};
    };

    const updateDayData = (date: string, updates: Partial<DayData>) => {
        const newDayData = [...dayData];
        const existingIndex = newDayData.findIndex((d) => d.date === date);

        if (existingIndex >= 0) {
            newDayData[existingIndex] = {...newDayData[existingIndex], ...updates};
        } else {
            newDayData.push({date, events: [], ...updates});
        }

        setDayData(newDayData);
        onDayDataChange?.(newDayData);
    };

    const shiftGroupDayCategoryRules = wishShiftRules ?? (availabilityShiftRule ? [availabilityShiftRule] : []);
    const wholeDayCategoryIds = new Set(shiftGroupDayCategoryRules.map((rule) => rule.categoryId));
    const shiftCategoryIdsWithWholeDayRules = new Set(shiftGroupDayCategoryRules.map((rule) => rule.eventCategoryId));
    const shiftTitlesControlledByRules = new Set(shiftGroupDayCategoryRules.flatMap((rule) => rule.eventTitles));

    const getWholeDayCategoryFromCompleteShiftGroup = (events: Event[]) => {
        const matchingRule = shiftGroupDayCategoryRules.find((rule) => {
            const selectedShiftTitles = new Set(
                events
                    .filter((event) => event.categoryId === rule.eventCategoryId)
                    .map((event) => event.title)
            );

            return rule.eventTitles.every((shiftTitle) => selectedShiftTitles.has(shiftTitle));
        });

        return matchingRule?.categoryId;
    };

    const setCategory = (date: string, categoryId: string | undefined) => {
        const selectedWholeDayRule = shiftGroupDayCategoryRules.find((rule) => rule.categoryId === categoryId);

        if (selectedWholeDayRule) {
            const current = getDayData(date);
            const eventsOutsideControlledShiftGroups = current.events.filter((event) => (
                !shiftTitlesControlledByRules.has(event.title) || !shiftCategoryIdsWithWholeDayRules.has(event.categoryId ?? '')
            ));
            const fullDayShiftEvents = selectedWholeDayRule.eventTitles.map((title, index) => ({
                id: `${date}-${selectedWholeDayRule.eventCategoryId}-${title}-${index}`,
                title,
                categoryId: selectedWholeDayRule.eventCategoryId,
            }));

            updateDayData(date, {categoryId, events: [...eventsOutsideControlledShiftGroups, ...fullDayShiftEvents]});
            return;
        }

        if (shiftGroupDayCategoryRules.length > 0 && categoryId === undefined) {
            const current = getDayData(date);
            updateDayData(date, {
                categoryId,
                events: current.events.filter((event) => !shiftCategoryIdsWithWholeDayRules.has(event.categoryId ?? '')),
            });
            return;
        }

        updateDayData(date, {categoryId});
    };

    const toggleRestrictedEvent = (date: string, eventCat: EventCategory, title: string, active: boolean) => {
        const current = getDayData(date);
        let updatedEvents = [...current.events];

        if (active) {
            const index = updatedEvents.findIndex(
                (event) => event.categoryId === eventCat.id && event.title === title
            );
            if (index !== -1) {
                updatedEvents.splice(index, 1);
            }
        } else {
            updatedEvents = [
                ...updatedEvents.filter((event) => (
                    event.title !== title ||
                    event.categoryId === eventCat.id ||
                    !shiftCategoryIdsWithWholeDayRules.has(event.categoryId ?? '')
                )),
                {
                    id: `${date}-${++eventIdCounter.current}`,
                    title,
                    categoryId: eventCat.id,
                },
            ];
        }

        if (shiftCategoryIdsWithWholeDayRules.has(eventCat.id)) {
            const matchingWholeDayCategoryId = getWholeDayCategoryFromCompleteShiftGroup(updatedEvents);

            updateDayData(date, {
                categoryId: matchingWholeDayCategoryId ?? (wholeDayCategoryIds.has(current.categoryId ?? '') ? undefined : current.categoryId),
                events: updatedEvents,
            });
            return;
        }

        updateDayData(date, {events: updatedEvents});
    };

    const addEvent = (date: string, title: string, categoryId?: string) => {
        const current = getDayData(date);
        const newEvent: Event = {
            id: `${date}-${++eventIdCounter.current}`,
            title,
            categoryId,
        };
        updateDayData(date, {events: [...current.events, newEvent]});
        setNewEventTitle({...newEventTitle, [date]: ""});
        setSelectedEventCategory({...selectedEventCategory, [date]: null});
        setPopoverMode({...popoverMode, [date]: "overview"});
    };

    const removeEvent = (date: string, eventId: string) => {
        const current = getDayData(date);
        updateDayData(date, {
            events: current.events.filter((e) => e.id !== eventId),
        });
    };

    const getCategoryColor = (categoryId?: string) => {
        if (!categoryId) return "transparent";
        return categories.find((c) => c.id === categoryId)?.color || "transparent";
    };

    const getCategoryName = (categoryId?: string) => {
        if (!categoryId) return null;
        return categories.find((c) => c.id === categoryId)?.name;
    };

    const getEventCategoryName = (categoryId?: string) => {
        if (!categoryId) return null;
        return eventCategories.find((c) => c.id === categoryId)?.name;
    };

    const getTextColorForBackground = (backgroundColor?: string) => {
        if (!backgroundColor?.startsWith("#")) return undefined;

        const hex = backgroundColor.slice(1);
        if (hex.length !== 6) return undefined;

        const red = parseInt(hex.slice(0, 2), 16);
        const green = parseInt(hex.slice(2, 4), 16);
        const blue = parseInt(hex.slice(4, 6), 16);
        const luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255;

        return luminance > 0.55 ? "#111827" : "#ffffff";
    };

    // Render calendar data.
    const daysInMonth = getDaysInMonth(month, year);
    const firstDay = getFirstDayOfMonth(month, year);
    const weekDays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
    const monthNames = [
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ];

    // Precompute the leading days from the previous month.
    const prevMonth = month === 1 ? 12 : month - 1;
    const prevYear = month === 1 ? year - 1 : year;
    const daysInPrevMonth = getDaysInMonth(prevMonth, prevYear);

    const calendarDays: Array<{ day: number; isCurrentMonth: boolean }> = [];

    if (view === "month") {
        // Fill the grid with trailing days from the previous month.
        for (let i = firstDay - 1; i >= 0; i--) {
            calendarDays.push({day: daysInPrevMonth - i, isCurrentMonth: false});
        }

        // Add the current month days.
        for (let day = 1; day <= daysInMonth; day++) {
            calendarDays.push({day, isCurrentMonth: true});
        }
    } else {
        for (let day = 1; day <= 7; day++) {
            calendarDays.push({day, isCurrentMonth: true});
        }
    }

    return (
        <Card className={className}>
            <CardHeader>
                <CardTitle className="text-center">
                    {view === "month" ? `${monthNames[month - 1]} ${year}` : `Musterwoche`}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-7 gap-2">
                    {/* Weekday header */}
                    {weekDays.map((day) => (
                        <div key={day} className="text-center p-2 font-medium">
                            {day}
                        </div>
                    ))}

                    {/* Calendar day cells */}
                    {calendarDays.map((dayObj, index) => {
                        const {day, isCurrentMonth} = dayObj;

                        // Previous-month filler days stay dimmed and non-interactive.
                        if (!isCurrentMonth) {
                            return (
                                <div
                                    key={`prev-${index}`}
                                    className="border rounded-lg p-2 text-left relative min-h-24 flex flex-col opacity-30 bg-gray-50"
                                >
                                    <div className="mb-1 text-gray-400">{day}</div>
                                </div>
                            );
                        }

                        const date = formatDate(day);
                        const data = getDayData(date);
                        const bgColor = getCategoryColor(data.categoryId);
                        const categoryName = getCategoryName(data.categoryId);

                        return (
                            <Popover
                                key={date}
                                open={openPopover === date}
                                onOpenChange={(open) => setOpenPopover(open ? date : null)}
                            >
                                <PopoverTrigger asChild>
                                    <button
                                        className="border rounded-lg p-2 hover:border-gray-400 transition-colors text-left relative min-h-24 flex flex-col"
                                        style={{backgroundColor: bgColor}}
                                    >
                                        <div className="mb-1">{day}</div>

                                        {/* Show events grouped by category when applicable. */}
                                        <div className="flex-1 flex flex-wrap gap-1 content-start overflow-hidden">
                                            {allowedEventTitles
                                                ? // Grouped mode: one badge per eventCategory
                                                eventCategories.map((eventCat) => {
                                                    const titles = data.events
                                                        .filter((e) => e.categoryId === eventCat.id)
                                                        .map((e) => e.title);
                                                    if (titles.length === 0) return null;

                                                    const sortedTitles = sortShiftTitles(titles);
                                                    const uniqueTitles = Array.from(new Set(sortedTitles));

                                                    return (
                                                        <div
                                                            key={eventCat.id}
                                                            className="text-xs px-1.5 py-0.5 rounded border font-medium"
                                                            style={{
                                                                backgroundColor: eventCat.color,
                                                                borderColor: eventCat.color,
                                                                color: getTextColorForBackground(eventCat.color),
                                                            }}
                                                        >
                                                            {uniqueTitles.join(', ')}
                                                        </div>
                                                    );
                                                })
                                                : // Free-text mode: individual badges
                                                (allowedEventTitles
                                                        ? // when allowedEventTitles is set we want the events sorted by canonical order
                                                        sortEventsByShiftOrder(data.events)
                                                            .slice(0, maxVisibleEvents ?? undefined)
                                                        : (maxVisibleEvents !== undefined
                                                                ? data.events.slice(0, maxVisibleEvents)
                                                                : data.events
                                                        )
                                                ).map((event) => (
                                                    <div
                                                        key={event.id}
                                                        className="text-xs px-1.5 py-0.5 rounded truncate border max-w-full"
                                                        style={{
                                                            backgroundColor: event.categoryId
                                                                ? eventCategories.find((c) => c.id === event.categoryId)?.color
                                                                : "rgba(255, 255, 255, 0.6)",
                                                            borderColor: event.categoryId
                                                                ? eventCategories.find((c) => c.id === event.categoryId)?.color
                                                                : "rgb(209, 213, 219)",
                                                        }}
                                                    >
                                                        {event.title}
                                                    </div>
                                                ))
                                            }
                                            {!allowedEventTitles && maxVisibleEvents !== undefined &&
                                                data.events.length > maxVisibleEvents && (
                                                    <div className="text-xs text-gray-600 px-1.5">
                                                        +{data.events.length - maxVisibleEvents} mehr
                                                    </div>
                                                )}
                                        </div>

                                        {showCategoryTitle && categoryName && (
                                            <div className="text-xs mt-auto pt-1 truncate opacity-80">
                                                {categoryName}
                                            </div>
                                        )}
                                    </button>
                                </PopoverTrigger>
                                <PopoverContent
                                    className="w-80 max-h-[min(520px,var(--radix-popover-content-available-height))] overflow-y-auto overscroll-contain"
                                    align="start"
                                    container={container}
                                    onWheel={(event) => event.stopPropagation()}
                                    onTouchMove={(event) => event.stopPropagation()}
                                >
                                    {/* Overview mode */}
                                    {(!popoverMode[date] || popoverMode[date] === "overview") && (
                                        <div className="space-y-4">
                                            <div>
                                                <h3 className="mb-2">
                                                    {view === "month" ? `${day}. ${monthNames[month - 1]} ${year}` : `Standard ${weekDays[day - 1]}`}

                                                </h3>
                                            </div>

                                            {/* Choose the day category */}
                                            <div>
                                                <Label>Kategorie</Label>
                                                <div className="flex flex-wrap gap-2 mt-2">
                                                    <Button
                                                        variant={data.categoryId === undefined ? "default" : "outline"}
                                                        size="sm"
                                                        onClick={() => setCategory(date, undefined)}
                                                        disabled={readOnly}
                                                    >
                                                        Keine
                                                    </Button>
                                                    {categories.map((category) => (
                                                        <Button
                                                            key={category.id}
                                                            variant={data.categoryId === category.id ? "default" : "outline"}
                                                            size="sm"
                                                            onClick={() => setCategory(date, category.id)}
                                                            disabled={readOnly}
                                                            style={{
                                                                backgroundColor:
                                                                    data.categoryId === category.id
                                                                        ? category.color
                                                                        : "transparent",
                                                                borderColor: category.color,
                                                            }}
                                                        >
                                                            {category.name}
                                                        </Button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Restricted shift selection (for example F/S/N) */}
                                            {allowedEventTitles && !readOnly && eventCategories.length > 0 && (
                                                <div className="space-y-3">
                                                    <Label>Schichten</Label>
                                                    {eventCategories.map((eventCat) => {
                                                        const activeTitles = new Set(
                                                            data.events
                                                                .filter((e) => e.categoryId === eventCat.id)
                                                                .map((e) => e.title)
                                                        );
                                                        return (
                                                            <div key={eventCat.id} className="space-y-1.5">
                              <span
                                  className="text-xs font-medium px-2 py-0.5 rounded-full"
                                  style={{
                                      backgroundColor: eventCat.color,
                                      color: getTextColorForBackground(eventCat.color),
                                  }}
                              >
                                {eventCat.name}
                              </span>
                                                                <div className="flex gap-2 mt-1">
                                                                    {allowedEventTitles.map((title) => {
                                                                        const active = activeTitles.has(title);
                                                                        return (
                                                                            <button
                                                                                key={title}
                                                                                type="button"
                                                                                onClick={() => toggleRestrictedEvent(date, eventCat, title, active)}
                                                                                className={[
                                                                                    "w-10 h-10 rounded-lg text-sm font-semibold border-2 transition-all",
                                                                                    active
                                                                                        ? "border-transparent text-white shadow-sm"
                                                                                        : "border-dashed bg-transparent hover:border-solid",
                                                                                ].join(" ")}
                                                                                style={
                                                                                    active
                                                                                        ? {
                                                                                            backgroundColor: eventCat.color,
                                                                                            borderColor: eventCat.color,
                                                                                            color: getTextColorForBackground(eventCat.color),
                                                                                        }
                                                                                        : {
                                                                                            borderColor: eventCat.color,
                                                                                            color: eventCat.color
                                                                                        }
                                                                                }
                                                                            >
                                                                                {title}
                                                                            </button>
                                                                        );
                                                                    })}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}

                                            {/* Free-text events fallback when allowedEventTitles is not provided */}
                                            {!allowedEventTitles && (
                                                <div>
                                                    <Label>Termine</Label>

                                                    {/* Event-category buttons are only available outside read-only mode. */}
                                                    {!readOnly && eventCategories.length > 0 && (
                                                        <div className="flex flex-wrap gap-2 mt-2">
                                                            {eventCategories.map((eventCat) => (
                                                                <Button
                                                                    key={eventCat.id}
                                                                    variant="outline"
                                                                    size="sm"
                                                                    onClick={() => {
                                                                        setSelectedEventCategory({
                                                                            ...selectedEventCategory,
                                                                            [date]: eventCat.id
                                                                        });
                                                                        setPopoverMode({
                                                                            ...popoverMode,
                                                                            [date]: "add-event"
                                                                        });
                                                                    }}
                                                                    style={{
                                                                        borderColor: eventCat.color,
                                                                        backgroundColor: "transparent",
                                                                    }}
                                                                >
                                                                    {eventCat.name} hinzufügen
                                                                </Button>
                                                            ))}
                                                        </div>
                                                    )}

                                                    {/* Event list inside a scroll area */}
                                                    {data.events.length > 0 && (
                                                        <ScrollArea
                                                            className="h-[200px] mt-2"
                                                            onWheel={(e) => e.stopPropagation()}
                                                        >
                                                            <div className="space-y-2 pr-4">
                                                                {sortEventsByShiftOrder(data.events).map((event) => (
                                                                    <div
                                                                        key={event.id}
                                                                        className="flex items-center justify-between p-2 rounded"
                                                                        style={{
                                                                            backgroundColor: event.categoryId
                                                                                ? eventCategories.find((c) => c.id === event.categoryId)?.color
                                                                                : "rgb(243, 244, 246)",
                                                                            color: event.categoryId
                                                                                ? getTextColorForBackground(eventCategories.find((c) => c.id === event.categoryId)?.color)
                                                                                : undefined,
                                                                        }}
                                                                    >
                                                                        <div className="flex flex-col gap-1">
                                                                            <span
                                                                                className="text-sm">{event.title}</span>
                                                                            {event.categoryId && (
                                                                                <span className="text-xs opacity-70">
                                        {getEventCategoryName(event.categoryId)}
                                      </span>
                                                                            )}
                                                                        </div>
                                                                        {!readOnly && (
                                                                            <Button
                                                                                variant="ghost"
                                                                                size="sm"
                                                                                onClick={() => removeEvent(date, event.id)}
                                                                            >
                                                                                <X className="h-4 w-4"/>
                                                                            </Button>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </ScrollArea>
                                                    )}
                                                </div>
                                            )}

                                            {/* Show the event list in read-only mode even when titles are restricted. */}
                                            {allowedEventTitles && readOnly && data.events.length > 0 && (
                                                <div>
                                                    <Label>Schichten</Label>
                                                    <ScrollArea
                                                        className="h-[200px] mt-2"
                                                        onWheel={(e) => e.stopPropagation()}
                                                    >
                                                        <div className="space-y-2 pr-4">
                                                            {sortEventsByShiftOrder(data.events).map((event) => (
                                                                <div
                                                                    key={event.id}
                                                                    className="flex items-center justify-between p-2 rounded"
                                                                    style={{
                                                                        backgroundColor: event.categoryId
                                                                            ? eventCategories.find((c) => c.id === event.categoryId)?.color
                                                                            : "rgb(243, 244, 246)",
                                                                        color: event.categoryId
                                                                            ? getTextColorForBackground(eventCategories.find((c) => c.id === event.categoryId)?.color)
                                                                            : undefined,
                                                                    }}
                                                                >
                                                                    <div className="flex flex-col gap-1">
                                                                        <span className="text-sm">{event.title}</span>
                                                                        {event.categoryId && (
                                                                            <span className="text-xs opacity-70">
                                      {getEventCategoryName(event.categoryId)}
                                    </span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </ScrollArea>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Add-event mode is only used for free-text input. */}
                                    {!allowedEventTitles && popoverMode[date] === "add-event" && selectedEventCategory[date] && (
                                        <div className="space-y-4">
                                            <div className="text-sm text-gray-600">
                                                {day}. {monthNames[month - 1]} {year}
                                            </div>
                                            <div>
                                                <h3 className="mb-3">
                                                    {eventCategories.find((c) => c.id === selectedEventCategory[date])?.name} hinzufügen
                                                </h3>
                                                <Input
                                                    placeholder="Name eingeben"
                                                    value={newEventTitle[date] || ""}
                                                    onChange={(e) =>
                                                        setNewEventTitle({...newEventTitle, [date]: e.target.value})
                                                    }
                                                    onKeyDown={(e) => {
                                                        if (e.key === "Enter" && newEventTitle[date]?.trim()) {
                                                            addEvent(date, newEventTitle[date].trim(), selectedEventCategory[date] || undefined);
                                                        }
                                                    }}
                                                    autoFocus
                                                />
                                            </div>
                                            <div className="flex gap-2">
                                                <Button
                                                    className="flex-1"
                                                    onClick={() => {
                                                        if (newEventTitle[date]?.trim()) {
                                                            addEvent(date, newEventTitle[date].trim(), selectedEventCategory[date] || undefined);
                                                        }
                                                    }}
                                                    disabled={!newEventTitle[date]?.trim()}
                                                >
                                                    Speichern
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    className="flex-1"
                                                    onClick={() => {
                                                        setPopoverMode({...popoverMode, [date]: "overview"});
                                                        setSelectedEventCategory({
                                                            ...selectedEventCategory,
                                                            [date]: null
                                                        });
                                                        setNewEventTitle({...newEventTitle, [date]: ""});
                                                    }}
                                                >
                                                    Zurück
                                                </Button>
                                            </div>
                                        </div>
                                    )}
                                </PopoverContent>
                            </Popover>
                        );
                    })}
                </div>

                {/* Legend */}
                {showLegend && (categories.length > 0 || eventCategories.length > 0) && (
                    <div className="mt-6 space-y-3">
                        {categories.length > 0 && (
                            <div className="flex flex-wrap gap-3 items-center">
                                <span className="text-sm font-medium">Tag-Kategorien:</span>
                                {categories.map((category) => (
                                    <div key={category.id} className="flex items-center gap-2">
                                        <div
                                            className="w-4 h-4 rounded"
                                            style={{backgroundColor: category.color}}
                                        />
                                        <span className="text-sm">{category.name}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                        {eventCategories.length > 0 && (
                            <div className="flex flex-wrap gap-3 items-center">
                                <span className="text-sm font-medium">Termin-Kategorien:</span>
                                {eventCategories.map((category) => (
                                    <div key={category.id} className="flex items-center gap-2">
                                        <div
                                            className="w-4 h-4 rounded"
                                            style={{backgroundColor: category.color}}
                                        />
                                        <span className="text-sm">{category.name}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
