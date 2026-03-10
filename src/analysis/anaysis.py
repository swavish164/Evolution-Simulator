import pygame
import pandas as pd
import os

class LiveAnalysis:
    def __init__(self, screen: pygame.Surface, stats_dir: str = "stats",
                 panel_x: int = 700, panel_width: int = 700, panel_height: int = 700):
        self.screen = screen
        self.stats_dir = stats_dir
        self.panel_x = panel_x
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.traits = ['size', 'speed', 'vision', 'metabolism', 'max_age']
        self.reload_interval = 20
        self.tick_counter = 0
        self.prey_df = None
        self.predator_df = None
        self._load()

        self.BG = (0, 0, 0)
        self.TEXT = (200, 200, 200)
        self.GRID = (40, 40, 40)

        self.PREY_AVG = (34, 139, 34)
        self.PREY_MAX = (0, 255, 0)
        self.PRED_AVG = (139, 0, 0)
        self.PRED_MAX = (255, 0, 0)
        self.font = pygame.font.SysFont('consolas', 11)
        self.small_font = pygame.font.SysFont('consolas', 9)

    def _load(self):
        prey_path = os.path.join(self.stats_dir, 'prey_stats.csv')
        pred_path = os.path.join(self.stats_dir, 'predator_stats.csv')

        if os.path.exists(prey_path):
            try:
                self.prey_df = pd.read_csv(prey_path)
            except Exception:
                pass

        if os.path.exists(pred_path):
            try:
                self.predator_df = pd.read_csv(pred_path)
            except Exception:
                pass

    def _get_stats_over_time(self, df, trait: str, smooth: int = 15):
        if df is None or df.empty:
            return [], [], [], []

        grouped = df.groupby('birth_tick')[trait].agg(['mean', 'max']).reset_index()

        avg_smooth = grouped['mean'].rolling(window=smooth, min_periods=1).mean()
        max_smooth = grouped['max'].rolling(window=smooth, min_periods=1).mean()

        return (grouped['birth_tick'].tolist(),
                avg_smooth.tolist(),
                max_smooth.tolist(),
                grouped['birth_tick'].tolist())

    def _draw_graph(self, surface: pygame.Surface, rect: pygame.Rect,
                    ticks: list, prey_avg: list, prey_max: list,
                    pred_avg: list, pred_max: list, title: str):
        pygame.draw.rect(surface, self.BG, rect)
        pygame.draw.rect(surface, self.GRID, rect, 1)

        pad = 18
        inner = pygame.Rect(rect.x + pad, rect.y + pad,
                            rect.width - pad * 2, rect.height - pad * 2)

        for i in range(4):
            y = inner.y + (inner.height // 3) * i
            pygame.draw.line(surface, self.GRID,
                             (inner.x, y), (inner.x + inner.width, y))

        label = self.font.render(title, True, self.TEXT)
        surface.blit(label, (rect.x + 4, rect.y + 2))

        all_values = []
        if prey_avg:
            all_values.extend(prey_avg)
        if prey_max:
            all_values.extend(prey_max)
        if pred_avg:
            all_values.extend(pred_avg)
        if pred_max:
            all_values.extend(pred_max)

        if not all_values:
            no_data = self.small_font.render('no data', True, self.GRID)
            surface.blit(no_data, (inner.x + 4, inner.y + inner.height // 2))
            return

        min_v = min(all_values)
        max_v = max(all_values) if max(all_values) != min_v else min_v + 1
        min_t = min(ticks) if ticks else 0
        max_t = max(ticks) if ticks else 1
        if max_t == min_t:
            max_t = min_t + 1

        def to_px(t, v):
            x = inner.x + int((t - min_t) / (max_t - min_t) * inner.width) if max_t != min_t else inner.x
            y = inner.y + inner.height - int((v - min_v) / (max_v - min_v) * inner.height) if max_v != min_v else inner.y
            return x, y

        if prey_avg and len(prey_avg) >= 2:
            points = [to_px(t, v) for t, v in zip(ticks, prey_avg)]
            pygame.draw.lines(surface, self.PREY_AVG, False, points, 2)

        if prey_max and len(prey_max) >= 2:
            points = [to_px(t, v) for t, v in zip(ticks, prey_max)]
            pygame.draw.lines(surface, self.PREY_MAX, False, points, 1)

        if pred_avg and len(pred_avg) >= 2:
            points = [to_px(t, v) for t, v in zip(ticks, pred_avg)]
            pygame.draw.lines(surface, self.PRED_AVG, False, points, 2)

        if pred_max and len(pred_max) >= 2:
            points = [to_px(t, v) for t, v in zip(ticks, pred_max)]
            pygame.draw.lines(surface, self.PRED_MAX, False, points, 1)

        legend_y = rect.y + 12
        legend_x = rect.x + rect.width - 120

        pygame.draw.line(surface, self.PREY_AVG, (legend_x, legend_y), (legend_x + 8, legend_y), 2)
        prey_label = self.small_font.render('Prey avg', True, self.PREY_AVG)
        surface.blit(prey_label, (legend_x + 12, legend_y - 4))

        pygame.draw.line(surface, self.PREY_MAX, (legend_x, legend_y + 10), (legend_x + 8, legend_y + 10), 1)
        prey_max_label = self.small_font.render('Prey max', True, self.PREY_MAX)
        surface.blit(prey_max_label, (legend_x + 12, legend_y + 6))

        pygame.draw.line(surface, self.PRED_AVG, (legend_x, legend_y + 20), (legend_x + 8, legend_y + 20), 2)
        pred_label = self.small_font.render('Pred avg', True, self.PRED_AVG)
        surface.blit(pred_label, (legend_x + 12, legend_y + 16))

        pygame.draw.line(surface, self.PRED_MAX, (legend_x, legend_y + 30), (legend_x + 8, legend_y + 30), 1)
        pred_max_label = self.small_font.render('Pred max', True, self.PRED_MAX)
        surface.blit(pred_max_label, (legend_x + 12, legend_y + 26))

    def update(self, world_tick: int):
        self.tick_counter += 1
        if self.tick_counter >= self.reload_interval:
            self._load()
            self.tick_counter = 0

        panel_rect = pygame.Rect(self.panel_x, 0, self.panel_width, self.panel_height)
        pygame.draw.rect(self.screen, self.BG, panel_rect)

        pygame.draw.line(self.screen, (60, 60, 60),
                         (self.panel_x, 0), (self.panel_x, self.panel_height), 2)

        graph_height = self.panel_height // len(self.traits)

        for i, trait in enumerate(self.traits):
            prey_ticks, prey_avg, prey_max, _ = self._get_stats_over_time(self.prey_df, trait)
            pred_ticks, pred_avg, pred_max, _ = self._get_stats_over_time(self.predator_df, trait)

            ticks = prey_ticks if prey_ticks else pred_ticks

            rect = pygame.Rect(
                self.panel_x + 4,
                i * graph_height + 4,
                self.panel_width - 8,
                graph_height - 8
            )
            self._draw_graph(self.screen, rect, ticks, prey_avg, prey_max,
                           pred_avg, pred_max, trait.upper())

        tick_label = self.font.render(f'tick: {world_tick}', True, self.TEXT)
        self.screen.blit(tick_label, (self.panel_x + 8, self.panel_height - 16))