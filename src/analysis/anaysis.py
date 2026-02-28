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
        self._load()

        self.BG = (0, 0, 0)
        self.LINE = (220, 30, 30)
        self.TEXT = (200, 200, 200)
        self.GRID = (40, 40, 40)
        self.font = pygame.font.SysFont('consolas', 11)

    def _load(self):
        path = os.path.join(self.stats_dir, 'prey_stats.csv')
        if os.path.exists(path):
            try:
                self.prey_df = pd.read_csv(path)
            except Exception:
                pass

    def _max_over_time(self, trait: str, smooth: int = 15):
        if self.prey_df is None or self.prey_df.empty:
            return [], []
        grouped = self.prey_df.groupby('birth_tick')[trait].max().reset_index()
        smoothed = grouped[trait].rolling(window=smooth, min_periods=1).mean()
        return grouped['birth_tick'].tolist(), smoothed.tolist()

    def _draw_graph(self, surface: pygame.Surface, rect: pygame.Rect,
                    ticks: list, values: list, title: str):
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

        if not ticks or len(values) < 2:
            no_data = self.font.render('no data yet', True, self.GRID)
            surface.blit(no_data, (inner.x + 4, inner.y + inner.height // 2))
            return

        min_v = min(values)
        max_v = max(values) if max(values) != min_v else min_v + 1
        min_t = min(ticks)
        max_t = max(ticks) if max(ticks) != min_t else min_t + 1

        def to_px(t, v):
            x = inner.x + int((t - min_t) / (max_t - min_t) * inner.width)
            y = inner.y + inner.height - int((v - min_v) / (max_v - min_v) * inner.height)
            return x, y

        points = [to_px(t, v) for t, v in zip(ticks, values)]
        if len(points) >= 2:
            pygame.draw.lines(surface, self.LINE, False, points, 2)

        max_label = self.font.render(f'{max_v:.3f}', True, self.TEXT)
        min_label = self.font.render(f'{min_v:.3f}', True, self.TEXT)
        surface.blit(max_label, (inner.x, inner.y))
        surface.blit(min_label, (inner.x, inner.y + inner.height - 12))

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
            ticks, values = self._max_over_time(trait)
            rect = pygame.Rect(
                self.panel_x + 4,
                i * graph_height + 4,
                self.panel_width - 8,
                graph_height - 8
            )
            self._draw_graph(self.screen, rect, ticks, values,
                             f'MAX {trait.upper()}')

        tick_label = self.font.render(f'tick: {world_tick}', True, self.TEXT)
        self.screen.blit(tick_label, (self.panel_x + 8, self.panel_height - 16))