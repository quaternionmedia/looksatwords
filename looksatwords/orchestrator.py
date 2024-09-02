from .gatherer import GnewsGatherer
from .generator import GnewsGenerator
from .analyzer import Analyzer
from .visualizer import Visualizer
from .hud import hud




class Orchestrator:

    def __init__(self,
                 gatherers: list[GnewsGatherer] = [],
                 generators: list[GnewsGenerator] = []
                 ):
        self.gatherers = gatherers
        self.generators = generators
        self.visualizer = None

    def add_gatherer(self, gatherer: GnewsGatherer):
        self.gatherers.append(gatherer)

    def add_gatherers(self, gatherers: list[GnewsGatherer]):
        self.gatherers.extend(gatherers)

    def add_generator(self, generator: GnewsGenerator):
        self.generators.append(generator)

    def add_generators(self, generators: list[GnewsGenerator]):
        self.generators.extend(generators)

    @hud
    def hud_test(self, hud):
        import time
        task = hud.add_task("[cyan]Orchestrator:Testing HUD", total=10)
        for i in range(10):
            hud.update(task, advance=1)
            time.sleep(0.1)

    @hud
    def gather(self, hud, num_articles=3):
        for gatherer in self.gatherers:
            task_gather = hud.add_task(f"[cyan]Orchestrator:Gathering {gatherer.query} articles...", total=1)
            gatherer.gather()
            hud.update(task_gather, advance=1)

    @hud
    def save(self, hud):
        for gatherer in self.gatherers:
            task_save = hud.add_task(f"[cyan]Orchestrator:Saving {gatherer.query} articles...", total=1)
            gatherer.save()
            hud.update(task_save, advance=1)

    @hud
    def validate(self, hud):
        for gatherer in self.gatherers:
            task_validate = hud.add_task(f"[cyan]Orchestrator:Validating {gatherer.query} articles...", total=1)
            gatherer.validate()
            hud.update(task_validate, advance=1)

    @hud
    def generate(self, hud):
        for generator in self.generators:
            task_generate = hud.add_task(f"[cyan]Orchestrator:Generating articles...", total=1)
            generator.generate()
            hud.update(task_generate, advance=1)

    @hud
    def analyze(self, hud):
        self.analyzer = Analyzer(dfs=[gatherer.df for gatherer in self.gatherers])
        self.analyzer.gather()
        self.analyzer.build_words_df()
        self.analyzer.preprocess()
        self.analyzer.analyze()

    @hud
    def visualize(self, hud):
        self.visualizer = Visualizer()
        self.visualizer.df = self.analyzer.df
        self.visualizer.make_plots()