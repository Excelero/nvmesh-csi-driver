
LTE = '<='
GTE = '>='
GT = '>'
LT = '<'
EQ = '='

class SemVer(object):
    """
    minimal implementation of the semver Specs (https://semver.org/)
    """

    def __init__(self, major, minor, patch):
        self.major = major
        self.minor = minor
        self.patch = patch

    @staticmethod
    def parse(version_str):
        if version_str[0] == 'v':
            # accept v prefix
            version_str = version_str[1:]

        try:
            version_str = version_str.split('-')[0]
            parts = version_str.split('.')
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])
        except:
            raise ValueError('Could not parse %s as SemVer' % version_str)

        return SemVer(major, minor, patch)

    def __str__(self):
        return '{}.{}.{}'.format(self.major, self.minor, self.patch)

    def compare(self, other):
        if type(other) in (str, unicode):
            other = SemVer.parse(other)

        if self.major != other.major:
            return self.major - other.major

        if self.minor != other.minor:
            return self.minor - other.minor

        return self.patch - other.patch

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __lt__(self, other):
        return self.compare(other) < 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __gt__(self, other):
        return self.compare(other) > 0


class SemVerConstraint(object):

    def __init__(self, str):
        self.comparator = EQ
        self.semver = None
        self.parse(str)

    def parse(self, str):
        # example input '>=1.2.7' or '<1.3.0'
        if str[0:2] in [GTE, LTE]:
            # two symbol comparator
            self.comparator = str[0:2]
            self.semver = SemVer.parse(str[2:])
        elif str[0] in [LT, GT, EQ]:
            # single symbol comparator
            self.comparator = str[0]
            self.semver = SemVer.parse(str[1:])
        else:
            # no comparator - equals assumed
            self.comparator = EQ
            self.semver = SemVer.parse(str)

    def is_valid(self, other_semver):
        if self.comparator == GTE:
            return other_semver >= self.semver
        elif self.comparator == LTE:
            return other_semver <= self.semver
        elif self.comparator == GT:
            return other_semver > self.semver
        elif self.comparator == LT:
            return other_semver < self.semver
        elif self.comparator == EQ:
            return other_semver == self.semver
        else:
            raise ValueError('unknown comparator %s' % self.comparator)


class SemVerConstraintList(object):
    def __init__(self, str):
        self.str = str
        self.constraints = []
        self.parse(str)

    def parse(self, str):
        # exmaple input '>=1.2.7 <1.3.0'
        parts = str.split(' ')
        for p in parts:
            c = SemVerConstraint(p)
            self.constraints.append(c)

    def is_valid(self, other_semver):
        for c in self.constraints:
            if not c.is_valid(other_semver):
                return False

        return True
