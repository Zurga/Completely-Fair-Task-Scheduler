from time import time
import bintrees
import json
import getopt
import sys

tasks = []
time_slice = 45
num_timeslices = 8
tree = bintrees.RBTree()
exit = False
path = '/home/jim/.tasks.json'


class TaskTree:
    def __init__(self, tasks=None):
        self.tree = bintrees.RBTree()
        self.stats = tasks.get('stats')
        if tasks:
            self.add_tasks(tasks['tasks'])

    def task_weight(self, task, tasks):
        return task.weight / sum(task.weight for task in tasks)

    def add_tasks(self, task_dicts):
        if type(task_dicts) == dict:
            tasks = [Task(**task_dicts)]
        else:
            tasks = [Task(**task) for task in task_dicts]

        for task in tasks:
            self.tree.insert(task.weight, task)
        self.weigh()

    def weigh(self):
        tasks = self.tree.values()
        self.tree.clear()
        for task in tasks:
            task.weight = self.task_weight(task, tasks)
            # time = task.time * task.weight
            self.tree.insert(task.weight, task)

    def by_label(self, label):
        tasks = [(key, task) for key, task in self.tree.items() if label in task.label]
        if tasks:
            return tasks[0]
        return None

    def save(self, path):
        tasks = [dict(vars(task)) for task in self.tree.values()]
        with open(path, 'w') as fle:
            fle.write(json.dumps(tasks))

    def remove_task(self, task):
        self.tree.remove(task[0])
        self.weigh()

    def start_task(self, task):
        task.start_time = time()

    def pause_task(self, task):
        task.time = (time() - task.start_time) / 60
        del(task.start_time)

    def __repr__(self):
        total = 0
        print(self.stats['done'])
        for weight, task in self.tree.items():
            total += weight
            print(weight, task)

        return str(total)

    def __getitem__(self, name):
        return self.tree[name]


class Task:
    def __init__(self, label='', text='', nice=0, time=45, due_date=None,
                 weight=0):
        self.label = label
        self.text = text
        self.nice = int(nice)
        self.time = int(time)
        if weight:
            self.weight = weight
        else:
            self.weight = 1024 / 1.25**self.nice
        # if not due_date:
        #     self.due_date = datetime.now()
        # else:
        #     self.due_date = datetime.strptime(due_date, '%Y%m%d %H:%M')

    def __repr__(self):
        return '%s - %d - %d' % (self.label, self.nice, self.time)

    def __getitem__(self, name):
        return self.__dict__[name]


def get_tasks():
    with open(path, 'r') as fle:
        tasks = json.load(fle)
    return tasks


def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'ha:d:m:', ['task=', 'task='])
    except getopt.GetoptError:
        print('no arguments given')
        sys.exit(2)
    tasks = get_tasks()
    tasklist = TaskTree(tasks=tasks)

    for opt, arg in opts:
        if opt in ('-a', '--add-task'):
            print('adding taxs')
            label, nice, time = arg.split(',')
            tasklist.add_tasks({'label': label, 'nice': nice, 'time': time})

        elif opt in ('-d', '--delete-task'):
            tasklist.remove_task(tasklist[arg])

        elif opt in ('-m', '--add-task'):
            tasklist.find_task_by_label()

        elif opt in ('-s', '--start-task'):
            key, task = tasklist.find_task_by_label(arg)
            if task.__getattribute__('start_time'):
                tasklist.start_task(task)
                print('You are doing %s now!' % (task.label))
            else:
                print('Task %s has already started' % (task.label))

        elif opt in ('-p', '--pause-task'):
            key, task = tasklist.find_task_by_label(arg)
            if task.__getattribute__('start_time'):
                tasklist.pause_task(task)
            else:
                print('Task %s has not started' % (task.label))

        elif opt in ('-D', '--task-done'):
            key, task = tasklist.find_task_by_label(arg)
            if task.__getattribute__('start_time'):
                tasklist.remove_task(task)
                tasklist.stats['done'] += 1
            else:
                print('Task %s has not started' % (task.label))

    print(tasklist)
    tasklist.save(path)
    return tasklist


if __name__ == '__main__':
    tasklist = main(sys.argv[1:])
