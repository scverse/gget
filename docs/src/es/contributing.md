[<kbd> Ver el codigo fuente de la pagina en GitHub </kbd>](https://github.com/pachterlab/gget/blob/main/docs/src/es/contributing.md)

# Bienvenido a la guía de contribución de gget

¡Gracias por invertir su tiempo en contribuir con nuestro proyecto! Cualquier contribución que hagas se verá reflejada en el [repositorio de GitHub de gget](https://github.com/pachterlab/gget). ✨

Lea nuestro [Código de conducta](./code_of_conduct.md) para mantener nuestra comunidad accesible y respetable.

En esta guía, obtendrá una descripción general del flujo de trabajo de contribución desde la creación de un GitHub Issue (asunto) o la creación de un GitHub Pull Request (PR) hasta la revisión y fusión de un PR.

## Issues (asuntos)

### Crear un nuevo Issue

Si detecta un problema con gget o tiene una idea para una nueva función, [comproba si ya existe un Issue para este problema/sugerencia](https://github.com/pachterlab/gget/issues). Si no existe un Issue relacionado, puede abrir un nuevo Issue utilizando el [formulario correspondiente](https://github.com/pachterlab/gget/issues/new/choose).

### Resolver un Issue

Explore nuestros [Issues existentes](https://github.com/pachterlab/gget/issues) para encontrar uno que le interese. Puede restringir la búsqueda utilizando "labels" como filtros. Si encuentra un Issue en el que desea trabajar, puede abrir un PR con una solución.

## Contribuir a través de Pull Requests (PRs)

### Empezar

1. Bifurcar ("fork") el [repositorio de GitHub de gget](https://github.com/pachterlab/gget).
- Usando GitHub Desktop:
  - ["Getting started with GitHub Desktop"](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/getting-started-with-github-desktop) lo guiará a través de la configuración de Desktop.
  - Una vez que GitHub Desktop está configurado, puede usarlo para [bifurcar el repositorio](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/cloning-and-forking-repositories-from-github-desktop)!

- Usando la Terminal:
  - [Bifurca el repositorio](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) para que pueda realizar sus cambios sin afectando el proyecto original hasta que esté listo para fusionarlos.

2. ¡Cree una rama de trabajo y comience con sus cambios!

### Confirma sus actualizaciones

Confirme sus cambios una vez que esté satisfecho con ellos.

### ‼️ Auto-revisa lo siguiente antes de crear un PR ‼️

1. Revise el contenido para mantener precisión técnica.
2. Edite los cambios/comentarios de gramática, ortografía y adherencia al estilo general del código de gget existente.
3. Formatee su código usando ["black"](https://black.readthedocs.io/en/stable/getting_started.html).
4. Asegúrese de que las pruebas unitarias pasen:
    - Las dependencias de desarrollador se pueden instalar con `pip install -r dev-requirements.txt`
    - Ejecute pruebas unitarias existentes desde la carpeta de gget con `coverage run -m pytest -ra -v tests && coverage report --omit=main.py,tests*`
5. Agregue nuevas pruebas unitarias si corresponde:
    - Los parámetros y los resultados esperados se pueden encontrar en archivos json en ./tests/fixtures/
    - Las pruebas unitarias se pueden agregar a ./tests/test_*.py y serán detectado automáticamente
6. Asegúrese de que las ediciones sean compatibles tanto con Python como con la Terminal
    - Los parámetros para la Terminal se definen en ./gget/main.py
8. Agregue módulos/argumentos nuevos a la documentación, si corresponde:
    - El manual de cada módulo se puede agregar/editar en `./docs/src/en/*.md` (la versión en español de la documentación en `./docs/src/es/*.md` se genera/actualiza automáticamente, y no necesita ser editada manualmente)

Si tiene alguna pregunta, no dude en iniciar una [discusión](https://github.com/pachterlab/gget/discussions) o crear un Issue como se describe anteriormente.

### Crear un Pull Request (PR)

Cuando haya terminado con los cambios, [cree un Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request), también conocido como "PR".

‼️ Realice todos los PRs contra la rama `dev` del repositorio gget

- No olvide de [vincular su PR con un Issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) si estás resolviendo uno.
- Habilite la casilla de verificación para [permitir ediciones del mantenedor](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/allowing-changes-to-a-pull-request-branch-created-from-a-fork) para que la rama se pueda actualizar para una fusión.
- Si se encuentra con problemas durante la fusión, consulte este [tutorial de git](https://github.com/skills/resolve-merge-conflicts) para ayudarlo a resolver conflictos de fusión y otros problemas.

Una vez que envíe su PR, un miembro del equipo gget revisará su propuesta. Podemos hacer preguntas o solicitar información adicional.

### ¡Su PR está fusionado!

¡Felicidades! 🎉	 El equipo de gget te lo agradece. ✨

Una vez que su PR se fusione, sus contribuciones serán visibles públicamente en el [repositorio de gget](https://github.com/pachterlab/gget).
