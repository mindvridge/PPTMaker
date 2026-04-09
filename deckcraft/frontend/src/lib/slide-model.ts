import { z } from "zod";

// ─── Hex color pattern ───────────────────────────────────────────────
const hexColor = z.string().regex(/^#[0-9a-fA-F]{6}$/);

// ─── ColorPalette ────────────────────────────────────────────────────
export const ColorPaletteSchema = z.object({
  primary: hexColor,
  secondary: hexColor,
  accent: hexColor,
  background: hexColor,
  surface: hexColor,
  text_primary: hexColor,
  text_secondary: hexColor,
});
export type ColorPalette = z.infer<typeof ColorPaletteSchema>;

// ─── Fonts ───────────────────────────────────────────────────────────
export const FontsSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  body: z.string(),
  caption: z.string(),
});
export type Fonts = z.infer<typeof FontsSchema>;

// ─── StylePreset ─────────────────────────────────────────────────────
export const StylePreset = z.enum([
  "modern_minimal",
  "corporate",
  "creative",
  "academic",
]);
export type StylePreset = z.infer<typeof StylePreset>;

// ─── DesignSystem ────────────────────────────────────────────────────
export const DesignSystemSchema = z.object({
  color_palette: ColorPaletteSchema,
  fonts: FontsSchema,
  style_preset: StylePreset,
});
export type DesignSystem = z.infer<typeof DesignSystemSchema>;

// ─── LayoutType ──────────────────────────────────────────────────────
export const LayoutType = z.enum([
  "title_hero",
  "title_image",
  "content_bullets",
  "two_column",
  "three_column",
  "image_text_left",
  "image_text_right",
  "full_image",
  "chart_with_text",
  "comparison",
  "timeline",
  "stats_kpi",
  "quote",
  "section_header",
  "table",
  "ending",
  "blank",
]);
export type LayoutType = z.infer<typeof LayoutType>;

// ─── Position (퍼센트 0-100) ─────────────────────────────────────────
export const PositionSchema = z.object({
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  width: z.number().min(0).max(100),
  height: z.number().min(0).max(100),
});
export type Position = z.infer<typeof PositionSchema>;

// ─── TextProps ───────────────────────────────────────────────────────
export const TextPropsSchema = z.object({
  content: z.string(),
  font_family: z.string(),
  font_size: z.number().min(1),
  font_weight: z.enum(["normal", "bold"]),
  color: z.string(),
  align: z.enum(["left", "center", "right"]),
  vertical_align: z.enum(["top", "middle", "bottom"]),
  line_height: z.number().optional(),
});
export type TextProps = z.infer<typeof TextPropsSchema>;

// ─── ImageProps ──────────────────────────────────────────────────────
export const ImagePropsSchema = z.object({
  src: z.string(),
  alt: z.string(),
  fit: z.enum(["cover", "contain", "fill"]),
  ai_prompt: z.string().optional(),
  border_radius: z.number().min(0).optional(),
});
export type ImageProps = z.infer<typeof ImagePropsSchema>;

// ─── ShapeProps ──────────────────────────────────────────────────────
export const ShapePropsSchema = z.object({
  shape_type: z.enum(["rectangle", "circle", "triangle", "line", "arrow"]),
  fill: z.string(),
  stroke: z.string().optional(),
  stroke_width: z.number().min(0).optional(),
  border_radius: z.number().min(0).optional(),
});
export type ShapeProps = z.infer<typeof ShapePropsSchema>;

// ─── ChartProps ──────────────────────────────────────────────────────
export const ChartDatasetSchema = z.object({
  label: z.string(),
  values: z.array(z.number()),
  color: z.string().optional(),
});

export const ChartPropsSchema = z.object({
  chart_type: z.enum(["bar", "line", "pie", "donut", "area"]),
  data: z.object({
    labels: z.array(z.string()),
    datasets: z.array(ChartDatasetSchema),
  }),
  show_legend: z.boolean().default(true),
});
export type ChartProps = z.infer<typeof ChartPropsSchema>;

// ─── TableProps ──────────────────────────────────────────────────────
export const TablePropsSchema = z.object({
  headers: z.array(z.string()),
  rows: z.array(z.array(z.string())),
  style: z.enum(["striped", "bordered", "minimal"]).default("striped"),
});
export type TableProps = z.infer<typeof TablePropsSchema>;

// ─── Background ──────────────────────────────────────────────────────
export const GradientSchema = z.object({
  from: z.string(),
  to: z.string(),
  direction: z.number(),
});

export const BackgroundSchema = z.object({
  type: z.enum(["solid", "gradient", "image"]),
  color: z.string().optional(),
  gradient: GradientSchema.optional(),
  image: ImagePropsSchema.optional(),
});
export type Background = z.infer<typeof BackgroundSchema>;

// ─── SlideElement ────────────────────────────────────────────────────
export const SlideElementSchema = z.object({
  id: z.string().uuid(),
  type: z.enum(["text", "image", "shape", "chart", "icon", "table"]),
  position: PositionSchema,
  rotation: z.number().default(0),
  opacity: z.number().min(0).max(1).default(1),
  z_index: z.number().int(),
  text_props: TextPropsSchema.optional(),
  image_props: ImagePropsSchema.optional(),
  shape_props: ShapePropsSchema.optional(),
  chart_props: ChartPropsSchema.optional(),
  table_props: TablePropsSchema.optional(),
});
export type SlideElement = z.infer<typeof SlideElementSchema>;

// ─── Slide ───────────────────────────────────────────────────────────
export const SlideSchema = z.object({
  id: z.string().uuid(),
  order: z.number().int().min(0),
  layout_type: LayoutType,
  background: BackgroundSchema,
  elements: z.array(SlideElementSchema),
  speaker_notes: z.string(),
  transition: z.string().optional(),
});
export type Slide = z.infer<typeof SlideSchema>;

// ─── Metadata ────────────────────────────────────────────────────────
export const MetadataSchema = z.object({
  created_at: z.string().datetime(),
  language: z.enum(["ko", "en"]),
  aspect_ratio: z.enum(["16:9", "4:3"]),
});
export type Metadata = z.infer<typeof MetadataSchema>;

// ─── Presentation (root) ────────────────────────────────────────────
export const PresentationSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  design_system: DesignSystemSchema,
  slides: z.array(SlideSchema).min(1),
  metadata: MetadataSchema,
});
export type Presentation = z.infer<typeof PresentationSchema>;
