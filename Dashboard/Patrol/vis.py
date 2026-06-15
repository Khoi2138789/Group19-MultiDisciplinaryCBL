import pygame

from Dashboard.Patrol.graph import Graph, Node
from Dashboard.Patrol.path import Path
from Dashboard.Patrol.walker import Walker


class GraphRenderer:
    def __init__(self, graph: Graph):
        pygame.init()

        self.path = None
        self.watcher = None

        self.graph = graph

        self.width = 1920
        self.height = 1080

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE
        )

        pygame.display.set_caption("Interactive Graph")

        self.background_color = (15, 15, 20)
        self.edge_color = (80, 80, 90)

        self.node_radius = 20

        self.camera_x = 0
        self.camera_y = 0

        self.zoom = 1.0

        self.dragging_node = None
        self.dragging_camera = False

        self.last_mouse_pos = (0, 0)

    def attach_simulation(self, walker, path):
        self.watcher = walker
        self.path = path

    def world_to_screen(self, x, y):
        sx = (x + self.camera_x) * self.zoom
        sy = (y + self.camera_y) * self.zoom
        return sx, sy

    def screen_to_world(self, x, y):
        wx = x / self.zoom - self.camera_x
        wy = y / self.zoom - self.camera_y
        return wx, wy

    def node_color(self, node):

        # base value shading (center darker, edges brighter etc)
        values = [n.value for n in self.graph.nodes]

        min_v, max_v = min(values), max(values)

        if max_v == min_v:
            base = 180
        else:
            t = (node.value - min_v) / (max_v - min_v)
            base = int(50 + t * 200)

        r = base
        g = base
        b = base

        if self.path:
            p = self.path.penalty(node)

            if p > 0:
                glow = int(255 * p)

                # push toward red
                r = min(255, r + glow)
                g = max(0, g - glow // 2)
                b = max(0, b - glow // 2)

        return (r, g, b)

    def get_node_at_screen_pos(self, mx, my):
        wx, wy = self.screen_to_world(mx, my)

        for node in reversed(self.graph.nodes):
            dx = node.x - wx
            dy = node.y - wy

            dist_sq = dx * dx + dy * dy

            if dist_sq <= self.node_radius ** 2:
                return node

        return None

    def centre_screen_to_node(self, node):
        self.camera_x = node.x
        self.camera_y = -node.y

    def draw(self):
        self.screen.fill(self.background_color)

        for a, b in self.graph.edges:
            ax, ay = self.world_to_screen(a.x, a.y)
            bx, by = self.world_to_screen(b.x, b.y)

            pygame.draw.line(
                self.screen,
                self.edge_color,
                (ax, ay),
                (bx, by),
                2
            )

        if self.path and len(self.path.history) > 1:

            history = list(self.path.history)

            max_len = len(history)

            for i in range(max_len - 1):

                a = history[i]
                b = history[i + 1]

                # 0 = oldest, 1 = newest
                t = i / max_len

                # fade out older segments
                intensity = int(255 * t)

                color = (0, intensity, 255)

                pygame.draw.line(
                    self.screen,
                    color,
                    self.world_to_screen(a.x, a.y),
                    self.world_to_screen(b.x, b.y),
                    3
                )


        for node in self.graph.nodes:
            sx, sy = self.world_to_screen(node.x, node.y)

            pygame.draw.circle(
                self.screen,
                self.node_color(node),
                (int(sx), int(sy)),
                int(self.node_radius * self.zoom)
            )

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:

                # LEFT CLICK -> drag node
                if event.button == 1:
                    node = self.get_node_at_screen_pos(*event.pos)

                    if node:
                        self.dragging_node = node

                # MIDDLE CLICK -> pan camera
                elif event.button == 2:
                    self.dragging_camera = True
                    self.last_mouse_pos = event.pos

                # SCROLL UP -> zoom in
                elif event.button == 4:
                    self.zoom *= 1.1

                # SCROLL DOWN -> zoom out
                elif event.button == 5:
                    self.zoom /= 1.1


            if event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:
                    self.dragging_node = None

                elif event.button == 2:
                    self.dragging_camera = False

            if event.type == pygame.MOUSEMOTION:

                mx, my = event.pos

                # Drag node
                if self.dragging_node:
                    wx, wy = self.screen_to_world(mx, my)

                    self.dragging_node.x = wx
                    self.dragging_node.y = wy

                # Pan camera
                if self.dragging_camera:
                    dx = mx - self.last_mouse_pos[0]
                    dy = my - self.last_mouse_pos[1]

                    self.camera_x += dx / self.zoom
                    self.camera_y += dy / self.zoom

                    self.last_mouse_pos = event.pos

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.watcher.step_random()

        # keys = pygame.key.get_pressed()

        # if keys[pygame.K_SPACE]:
        #     self.watcher.step_random()

        return True

    def run(self):
        clock = pygame.time.Clock()

        running = True

        while running:
            running = self.handle_events()

            self.draw()

            clock.tick(60)

        pygame.quit()