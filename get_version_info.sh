DESCRIBE=$(git describe --long)
VERSION=$(echo "$DESCRIBE" | cut -f1 -d '-')
BUILD=$(echo "$DESCRIBE" | cut -f2 -d '-')
COMMIT=$(echo "$DESCRIBE" | cut -f3 -d '-')

if [ "$DESCRIBE" != "$(git describe)" ];then
	# git describe == git describe --long - this means we are building a commit that has a version tag
	DRIVER_VERSION="${VERSION}"
else
	DRIVER_VERSION="${VERSION}-${BUILD}"
fi

echo "DRIVER_VERSION=$DRIVER_VERSION"
echo "DESCRIBE=$DESCRIBE"
echo "VERSION=$VERSION"
echo "BUILD=$BUILD"
echo "COMMIT=$COMMIT"