import {
  House,
  Flag,
  Timer,
  Rocket,
  Trophy,
  Map as MapIcon,
  Library,
  User,
  Users,
  TrendingUp,
  CloudSun,
  Fuel,
  Sparkles,
  Medal,
  Settings,
  AlarmClock,
  Search,
  BarChart3,
  Calendar,
  MapPin,
  Droplets,
  CloudRain,
  Thermometer,
  Wind,
  Gauge,
  TriangleAlert,
  Check,
  X,
  Info,
  CircleCheck,
  CircleX,
  CircleAlert,
  Lightbulb,
  Target,
  Calculator,
  BookOpen,
  Car,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  RefreshCw,
  Clock,
  Database,
  ListChecks,
  Activity,
  CircleHelp,
  Zap,
  Plus,
  Pencil,
  Trash2,
  Star,
  ClipboardList,
  ExternalLink,
  Bot,
  HardHat,
  Hourglass,
  type LucideIcon,
} from 'lucide-react';

export const ICONS = {
  home: House,
  flag: Flag,
  timer: Timer,
  rocket: Rocket,
  trophy: Trophy,
  map: MapIcon,
  circuit: MapPin,
  library: Library,
  user: User,
  users: Users,
  team: Car,
  car: Car,
  'trending-up': TrendingUp,
  weather: CloudSun,
  fuel: Fuel,
  crystal: Sparkles,
  sparkles: Sparkles,
  medal: Medal,
  settings: Settings,
  alarm: AlarmClock,
  search: Search,
  chart: BarChart3,
  calendar: Calendar,
  pin: MapPin,
  droplet: Droplets,
  rain: CloudRain,
  thermometer: Thermometer,
  wind: Wind,
  gauge: Gauge,
  warning: TriangleAlert,
  check: Check,
  x: X,
  info: Info,
  'check-circle': CircleCheck,
  'x-circle': CircleX,
  'alert-circle': CircleAlert,
  lightbulb: Lightbulb,
  target: Target,
  calculator: Calculator,
  book: BookOpen,
  'chevron-down': ChevronDown,
  'chevron-right': ChevronRight,
  'chevron-left': ChevronLeft,
  'arrow-right': ArrowRight,
  refresh: RefreshCw,
  clock: Clock,
  database: Database,
  tasks: ListChecks,
  activity: Activity,
  help: CircleHelp,
  zap: Zap,
  plus: Plus,
  edit: Pencil,
  trash: Trash2,
  star: Star,
  clipboard: ClipboardList,
  'external-link': ExternalLink,
  bot: Bot,
  worker: HardHat,
  hourglass: Hourglass,
} as const;

export type IconName = keyof typeof ICONS;

interface IconProps {
  name: IconName;
  size?: number;
  strokeWidth?: number;
  className?: string;
  color?: string;
  'aria-hidden'?: boolean;
}

export default function Icon({
  name,
  size = 18,
  strokeWidth = 2,
  className = '',
  color,
  'aria-hidden': ariaHidden = true,
}: IconProps) {
  const Cmp: LucideIcon = ICONS[name] ?? CircleHelp;
  return (
    <Cmp
      className={`icon ${className}`.trim()}
      size={size}
      strokeWidth={strokeWidth}
      color={color}
      aria-hidden={ariaHidden}
    />
  );
}
