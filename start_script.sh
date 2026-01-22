# Sicherstellen, dass wir im richtigen Branch sind und diesen aktualisieren
BRANCH="laptop_version"

echo "Verwerfen von lokalen Änderungen"
git reset --hard

echo "Wechseln zum Branch $BRANCH"
git checkout $BRANCH

echo "Aktualisieren des Branches"
git pull origin $BRANCH
